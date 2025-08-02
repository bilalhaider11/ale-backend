import re
import base64
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
    OrganizationPartnershipService,
    
)
from common.models import OrganizationPartnershipStatusEnum, OrganizationPartnership, PersonOrganizationRoleEnum
from app.helpers.decorators import login_required, organization_required

# Create the organization blueprint
organization_partnership_api = Namespace("organization_partnership", description="Organization partnership-related APIs")


@organization_partnership_api.route("/")
class OrganizationPartnerships(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        organization_partnership_service = OrganizationPartnershipService(config)
        partnerships = organization_partnership_service.get_all_partnerships_for_organization(
            organization.entity_id
        )
        return get_success_response(partnerships=partnerships)

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        organization_service = OrganizationService(config)
        organization_partnership_service = OrganizationPartnershipService(config)

        # Parse request body
        parsed_body = parse_request_body(
            request, ["subdomain", "message"]
        )
        message = parsed_body.pop("message", "")
        validate_required_fields(parsed_body)

        subdomain = parsed_body["subdomain"]

        receiver_organization = organization_service.get_organization_by_subdomain(subdomain)
        if not receiver_organization:
            return get_failure_response(
                message="No organization found with the provided subdomain."
            )
        
        if receiver_organization.entity_id == organization.entity_id:
            return get_failure_response(
                message="Cannot create a partnership with the same organization."
            )
        
        existing_partnership = organization_partnership_service.get_organization_partnership(
            organization.entity_id,
            receiver_organization.entity_id
        )

        if existing_partnership:
            if existing_partnership.status == OrganizationPartnershipStatusEnum.PENDING.value:
                return get_failure_response(
                    message="A partnership request is already pending with this organization."
                )
            elif existing_partnership.status == OrganizationPartnershipStatusEnum.ACTIVE.value:
                return get_failure_response(
                    message="A partnership already exists with this organization."
                )
            elif existing_partnership.status in [
                OrganizationPartnershipStatusEnum.DECLINED.value,
                OrganizationPartnershipStatusEnum.REVOKED.value,
                OrganizationPartnershipStatusEnum.CANCELLED.value,
            ]:
                # If partnership is declined or revoked, we can create a new one
                existing_partnership.status = OrganizationPartnershipStatusEnum.PENDING.value
                existing_partnership.requesting_organization_id = organization.entity_id
                existing_partnership.requested_by_id = person.entity_id
                existing_partnership.responded_by_id = None
                existing_partnership.message = message
                existing_partnership.created_at = None
                partnership = organization_partnership_service.save_organization_partnership(existing_partnership)
                partnership = organization_partnership_service.get_partnership_for_organization(partnership.entity_id, organization.entity_id)
                return get_success_response(
                    message="Partnership request re-sent successfully.",
                    partnership=partnership
                )

        else:
            partnership = OrganizationPartnership(
                requesting_organization_id=organization.entity_id,
                organization_1_id=organization.entity_id,
                organization_2_id=receiver_organization.entity_id,
                status=OrganizationPartnershipStatusEnum.PENDING.value,
                message=message,
                requested_by_id=person.entity_id
            )
            partnership = organization_partnership_service.save_organization_partnership(partnership)
            partnership = organization_partnership_service.get_partnership_for_organization(partnership.entity_id, organization.entity_id)
            return get_success_response(
                message="Partnership request sent successfully.",
                partnership=partnership
            )

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def put(self, person, organization):
        organization_service = OrganizationService(config)
        organization_partnership_service = OrganizationPartnershipService(config)

        # Parse request body
        parsed_body = parse_request_body(
            request, ["organization_partnership_id", "status"]
        )
        validate_required_fields(parsed_body)

        organization_partnership_id = parsed_body["organization_partnership_id"]
        status = parsed_body["status"]

        try:
            status = OrganizationPartnershipStatusEnum(status)
        except ValueError:
            return get_failure_response(
                message="Invalid status provided."
            )

        organization_partnership = organization_partnership_service.get_organization_partnership_by_id(
            organization_partnership_id
        )

        if organization_partnership.organization_can_transition_status(
            new_status=status,
            acting_organization_id=organization.entity_id
        ):
            organization_partnership.status = status.value
            if status in [
                OrganizationPartnershipStatusEnum.ACTIVE,
                OrganizationPartnershipStatusEnum.DECLINED
            ]:
                organization_partnership.responded_by_id = person.entity_id
            organization_partnership = organization_partnership_service.save_organization_partnership(organization_partnership)
            organization_partnership = organization_partnership_service.get_partnership_for_organization(organization_partnership.entity_id, organization.entity_id)

            return get_success_response(
                message=f"Partnership status updated to {status.value}.",
                partnership=organization_partnership
            )
        else:
            return get_failure_response(
                message="Cannot transition partnership status from current state."
            )
