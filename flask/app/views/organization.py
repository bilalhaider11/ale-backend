from flask_restx import Namespace, Resource
from flask import request
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
    EmailService
)
from app.helpers.decorators import (login_required,
                                    organization_required,
                                    has_role
                                    )
from app.helpers.exceptions import APIException

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
    @organization_required(with_roles=["admin"])
    def put(self, organization):
        parsed_body = parse_request_body(request, ["name"])
        validate_required_fields(parsed_body)
        
        organization_service = OrganizationService(config)
        organization.name = parsed_body["name"]
        organization_service.save_organization(organization)

        return get_success_response(message="Organization updated successfully.", organization=organization)

@has_role("admin")
@organization_api.route('/<string:organization_id>/persons')
class OrganizationPersons(Resource):

    @login_required()
    def get(self, organization_id, person):
        organization_service = OrganizationService(config)

        # Retrieve the organization
        organization = organization_service.get_organization_by_id(organization_id)
        if not organization:
            return get_failure_response(message="Organization not found.", status_code=404)

        # Get all persons and their roles for this organization
        persons_with_roles = organization_service.get_persons_with_roles_in_organization(organization_id)
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

        # Parse request body
        parsed_body = parse_request_body(request, ['email', 'roles', 'first_name', 'last_name'])
        validate_required_fields({key: parsed_body[key] for key in invitation_service.REQUIRED_FIELDS})
        email = parsed_body['email']
        roles = parsed_body['roles']
        first_name = parsed_body.get('first_name')
        last_name = parsed_body.get('last_name')

        # Find or create person
        person_by_email = person_service.get_person_by_email_address(email)
        if not person_by_email:
            return get_failure_response(message="Person not found.", status_code=404)

        invited_person_id = person_by_email.entity_id
        organization = organization_service.get_organization_by_id(organization_id)
        if not organization:
            return get_failure_response(message="Organization not found.", status_code=404)

        # Check if the person already has any of the invited roles
        existing_roles = person_organization_role_service.get_roles_of_person_in_organization(invited_person_id, organization_id)
        already_assigned_roles = [role for role in roles if role in existing_roles]
        if already_assigned_roles:
            roles_str = ", ".join(already_assigned_roles)
            return get_failure_response(message=f"Person already has the role(s): {roles_str} in this organization.", status_code=400)

        # Create and send invitation
        invitation = invitation_service.create_invitation(
            organization_id=organization_id,
            invitee_id=person.entity_id,
            email=email,
            roles=roles,
            person_id=invited_person_id,
            first_name=first_name,
            last_name=last_name,
        )
        invitation_service.send_invitation_email(invitation, organization.name, person)

        return get_success_response(message=f"Invitation sent successfully.")


@organization_api.route('/accept-invitation/<string:token>')
class AcceptInvitation(Resource):
    @login_required()
    def get(self, token, person):
        person_organization_role_service = PersonOrganizationRoleService(config)
        invitation_service = PersonOrganizationInvitationService(config, person_organization_role_service)
        email_service = EmailService(config)

        try:
            # Decode token and get invitation
            payload = invitation_service.decode_invitation_token(token)
            invitation = invitation_service.get_invitation_by_token(token)

            if not invitation:
                return get_failure_response(message="Invalid or expired invitation.", status_code=400)

            # Verify person_id match
            if payload['person_id'] != person.entity_id:
                return get_failure_response(message="You are not authorized to accept this invitation.", status_code=403)

            # Verify email match
            user_email = email_service.get_email_by_email_address(invitation.email)

            if not user_email or user_email.email != invitation.email:
                return get_failure_response(message=f"You are not authorized to accept this invitation. {user_email}, {invitation.email} {person.entity_id}", status_code=403)

            # Accept invitation
            invitation_service.accept_invitation(invitation, person.entity_id)
            return get_success_response(message="Invitation accepted successfully.")
        except APIException as e:
            return get_failure_response(message=str(e), status_code=400)
