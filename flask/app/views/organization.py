from flask_restx import Namespace, Resource
from flask import request
from app.helpers.response import (
    get_success_response,
    get_failure_response,
    parse_request_body,
    validate_required_fields,
)
from common.app_config import config
from common.services import OrganizationService
from app.helpers.decorators import login_required, organization_required, has_role

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
