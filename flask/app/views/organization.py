from flask_restx import Namespace, Resource
from flask import request
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from common.app_config import config
from common.services import OrganizationService, PersonService
from app.helpers.decorators import login_required, organization_required

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
