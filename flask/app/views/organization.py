import re
from flask_restx import Namespace, Resource
from flask import request
from werkzeug.datastructures import FileStorage
from app.helpers.response import (
    get_success_response,
    get_failure_response,
    parse_request_body,
    validate_required_fields,
)
from common.app_config import config
from common.services import (
    OrganizationService,
    PersonOrganizationInvitationService,
    PersonOrganizationRoleService,
    PersonService,
    EmailService,
    PhoneNumberService
)
from common.models import PersonOrganizationRoleEnum, Person, PhoneNumber
from app.helpers.decorators import (login_required,
                                    organization_required,
                                    has_role
                                    )
from common.helpers.exceptions import APIException


from common.app_logger import logger

# Create the organization blueprint
organization_api = Namespace('organization', description="Organization-related APIs")

@organization_api.route('/')
class Organizations(Resource):
    
    @login_required()
    def get(self, person):
        
        organization_service = OrganizationService(config)
        organizations = organization_service.get_organizations_with_roles_by_person(person.entity_id)
        return get_success_response(organizations=organizations)

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def put(self, organization):
        organization_service = OrganizationService(config)
        
        # Get organization by ID to ensure it exists
        organization = organization_service.get_organization_by_id(organization.entity_id)
        
        # Extract and validate form data
        name = request.form.get("name")
        subdomain = request.form.get("subdomain")
        logo_file = request.files.get("logo")
        
        validate_required_fields({'name': name})

        updated_org = organization_service.update_organization_name(
            organization,
            {"name": name}
        )

        if not updated_org:
            return get_failure_response(
                message="Failed to update organization.",
                status_code=500
            )

        # Process subdomain if provided
        if subdomain is not None and subdomain.strip():
            if not re.match(r'^[a-z0-9-]+$', subdomain):
                return get_failure_response(
                    message="Subdomain must contain only lowercase letters, numbers, and hyphens.",
                    status_code=400
                )
            
            subdomain_result = organization_service.process_subdomain(organization, subdomain)

            if not subdomain_result:
                return get_failure_response(
                    message="Failed to process subdomain update.",
                    status_code=500
                )

        # Process logo file if provided
        if logo_file and isinstance(logo_file, FileStorage):
            logo_result = organization_service.upload_organization_logo(
                organization,
                logo_file
            )
            
            if not logo_result:
                return get_failure_response(
                    message="Failed to process organization logo",
                    status_code=500
                )

        return get_success_response(
            message="Organization updated successfully.",
            organization=updated_org
        )

@has_role("admin")
@organization_api.route('/<string:organization_id>/persons')
class OrganizationPersons(Resource):

    @login_required()
    def get(self, organization_id, person):
        organization_service = OrganizationService(config)
        person_organization_role_service = PersonOrganizationRoleService(config)

        # Retrieve the organization
        organization = organization_service.get_organization_by_id(organization_id)
        if not organization:
            return get_failure_response(message="Organization not found.", status_code=404)

        # Get all persons and their roles for this organization
        persons_with_roles = person_organization_role_service.get_persons_with_roles_in_organization(organization_id)
        return get_success_response(persons=persons_with_roles)

@has_role("admin")
@organization_api.route('/<string:organization_id>/invite')
class OrganizationInvite(Resource):
    @login_required()
    def post(self, organization_id, person):
            invitation_service = PersonOrganizationInvitationService(config)
            organization_service = OrganizationService(config)
            person_service = PersonService(config)
            person_organization_role_service = PersonOrganizationRoleService(config)
            phone_number_service = PhoneNumberService(config)
            email_service = EmailService(config)

            parsed_body = parse_request_body(
                request,
                ['email', 'roles', 'first_name', 'last_name', 'phone_number', 'entity_id']
            )

            entity_id = parsed_body.pop('entity_id', None)
            email = parsed_body.get('email')
            roles_raw = parsed_body.get('roles')
            first_name = parsed_body.get('first_name')
            last_name = parsed_body.get('last_name')
            phone_number = parsed_body.get('phone_number')

            organization = organization_service.get_organization_by_id(organization_id)
            if not organization:
                return get_failure_response(message="Organization not found.", status_code=404)

            # Normalize & validate roles
            try:
                roles = person_organization_role_service.normalize_roles(roles_raw)
                person_organization_role_service.validate_roles(roles)
            except ValueError as e:
                return get_failure_response(message=str(e), status_code=400)
                
            # Check if admin is trying to invite themselves
            admin_email = email_service.get_email_by_person_id(person.entity_id, email)
            if admin_email and admin_email.email == email:
                return get_failure_response(
                    message="You cannot invite yourself to an organization you already administer.",
                    status_code=400
                )
                
            # Check if user is already invited or has a pending invitation
            has_existing_invitation, error_message = invitation_service.check_existing_invitation(
                email, organization_id, entity_id
            )
            if has_existing_invitation:
                return get_failure_response(message=error_message, status_code=400)

            if entity_id:
                invitation = invitation_service.get_invitation_by_id(entity_id)
                if not invitation:
                    return get_failure_response(message="Invitation not found.", status_code=404)
                if invitation.organization_id != organization_id:
                    return get_failure_response(message="Invitation does not belong to this organization.", status_code=403)

                if invitation.invitee_id:
                    p = person_service.get_person_by_id(invitation.invitee_id)
                    if p and (p.first_name != first_name or p.last_name != last_name):
                        p.first_name = first_name
                        p.last_name = last_name
                        person_service.save_person(p)

                # If invite already accepted -> sync roles
                if invitation.status == 'active' and invitation.invitee_id:
                    current_roles = person_organization_role_service.get_roles_of_person_in_organization(invitation.invitee_id, organization_id)

                    if set(current_roles) != set(roles):
                        changes = person_organization_role_service.sync_roles(
                            person_id=invitation.invitee_id,
                            organization_id=organization_id,
                            desired_roles=roles
                        )

                # Update invitation data
                updated_invitation = invitation_service.update_invitation(
                    entity_id=entity_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    roles=roles
                )
                if not updated_invitation:
                    return get_failure_response(message="Failed to update invitation.", status_code=500)

                # Email / phone updates
                if invitation.invitee_id and email:
                    email_service.update_email_address(invitation.invitee_id, email)

                if phone_number and invitation.invitee_id:
                    existing_phone = phone_number_service.get_phone_number_by_person_id(invitation.invitee_id)
                    if existing_phone:
                        existing_phone.phone = phone_number
                        phone_number_service.save_phone_number(existing_phone)
                    else:
                        phone_number_service.save_phone_number(PhoneNumber(
                            phone=phone_number,
                            person_id=invitation.invitee_id
                        ))

                return get_success_response(message="Invitation updated successfully.", invitation=updated_invitation)

            # --- Create new invitation path ---
            validate_required_fields({key: parsed_body[key] for key in invitation_service.REQUIRED_FIELDS})

            person_by_email = person_service.get_person_by_email_address(email)
            if person_by_email:
                invited_person_id = person_by_email.entity_id
                existing_roles = person_organization_role_service.get_roles_of_person_in_organization(invited_person_id, organization_id)
                overlap = [r for r in roles if r in existing_roles]
                if overlap:
                    return get_failure_response(
                        message=f"Person already has the role(s): {', '.join(overlap)} in this organization.",
                        status_code=400
                    )
            else:
                new_person = person_service.save_person(Person(first_name=first_name, last_name=last_name))
                invited_person_id = new_person.entity_id

            invitation = invitation_service.create_invitation(
                organization_id=organization_id,
                invitee_id=invited_person_id,
                email=email,
                roles=roles,
                first_name=first_name,
                last_name=last_name,
                invited_by_id=person.entity_id
            )
            invitation_service.send_invitation_email(invitation, organization.name, person)

            if phone_number:
                existing_phone = phone_number_service.get_phone_number_by_person_id(invited_person_id)
                if existing_phone:
                    existing_phone.phone = phone_number
                    phone_number_service.save_phone_number(existing_phone)
                else:
                    phone_number_service.save_phone_number(PhoneNumber(
                        phone=phone_number,
                        person_id=invited_person_id
                    ))

            return get_success_response(message="Invitation sent successfully.")
    
    @login_required()
    def delete(self, organization_id, person):
        invitation_service = PersonOrganizationInvitationService(config)
        person_organization_role_service = PersonOrganizationRoleService(config)
        
        # Parse request body
        parsed_body = parse_request_body(request, ['entity_id'])
        validate_required_fields({'entity_id': parsed_body['entity_id']})
        
        entity_id = parsed_body['entity_id']
        
        # Get the invitation
        invitation = invitation_service.get_invitation_by_id(entity_id)

        if not invitation:
            return get_failure_response(message="Invitation not found.", status_code=404)
            
        # Verify the invitation belongs to this organization
        if invitation.organization_id != organization_id:
            return get_failure_response(message="Invitation does not belong to this organization.", status_code=403)
        
        # If the invitation has an associated person, delete their roles for this organization
        if invitation.invitee_id:
            # Delete all roles for this person in this organization
            person_organization_role_service.delete_roles_for_person_in_organization(
                person_id=invitation.invitee_id,
                organization_id=organization_id
            )
        
        # Delete the invitation
        deleted = invitation_service.delete_invitation(invitation)
        
        if not deleted:
            return get_failure_response(message="Failed to delete invitation.", status_code=500)
            
        return get_success_response(message="Invitation deleted successfully.")

@has_role("admin")        
@organization_api.route('/<string:organization_id>/resend_invite')
class OrganizationResendInvite(Resource):
    @login_required()
    def post(self, organization_id, person):
        invitation_service = PersonOrganizationInvitationService(config)
        organization_service = OrganizationService(config)
        
        # Parse request body
        parsed_body = parse_request_body(request, ['entity_id'])
        validate_required_fields({'entity_id': parsed_body['entity_id']})
        
        entity_id = parsed_body['entity_id']
        
        # Get the invitation
        invitation = invitation_service.get_invitation_by_id(entity_id)
        if not invitation:
            return get_failure_response(message="Invitation not found.", status_code=404)
            
        # Verify the invitation belongs to this organization
        if invitation.organization_id != organization_id:
            return get_failure_response(message="Invitation does not belong to this organization.", status_code=403)
        
        # Get the organization for its name
        organization = organization_service.get_organization_by_id(organization_id)
        if not organization:
            return get_failure_response(message="Organization not found.", status_code=404)
        
        # Resend the invitation
        try:
            invitation_service.resend_invitation(invitation, organization.name, person)
            return get_success_response(message="Invitation resent successfully.")
        except APIException as e:
            return get_failure_response(message=str(e), status_code=e.status_code if hasattr(e, 'status_code') else 400)


@organization_api.route('/accept-invitation/<string:token>')
class AcceptInvitation(Resource):

    def get(self, token):
        invitation_service = PersonOrganizationInvitationService(config)
        email_service = EmailService(config)
        person_service = PersonService(config)

        try:
            invitation = invitation_service.get_invitation_by_token(token)

            if not invitation:
                return get_failure_response(message="Invalid or expired invitation.", status_code=400)

            # Verify email match
            user_email = email_service.get_email_by_email_address(invitation.email)
            if not user_email or user_email.email != invitation.email:
                return get_failure_response(message="You are not authorized to accept this invitation.", status_code=403)
            
            person_by_email = person_service.get_person_by_email_address(user_email.email)

            # Accept invitation
            invitation_service.accept_invitation(invitation, person_by_email.entity_id)
            return get_success_response(message="Invitation accepted successfully.")
        except APIException as e:
            return get_failure_response(message=str(e), status_code=400)


@organization_api.route('/partners')
class OrganizationPartners(Resource):

    @login_required()
    @organization_required()
    def get(self, person, organization):
        organization_service = OrganizationService(config)
        organization_partners = organization_service.get_organization_partners(organization.entity_id)
        return get_success_response(data=organization_partners)
