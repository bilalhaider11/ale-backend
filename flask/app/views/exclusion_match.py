import os
import tempfile
from flask import request
from flask_restx import Namespace, Resource

from common.app_config import config
from common.services.current_employee import CurrentEmployeeService
from common.services.employee_exclusion_match import EmployeeExclusionMatchService
from common.services.oig_employees_exclusion import OigEmployeesExclusionService
from common.models.person_organization_role import PersonOrganizationRoleEnum
from app.helpers.response import get_success_response, get_failure_response, parse_request_body
from app.helpers.decorators import login_required, organization_required

exclusion_match_api = Namespace('exclusion_match', description='Exclusion match operations')


@exclusion_match_api.route('/status')
class EmployeeExclusionMatchStatus(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """
        Upload a CSV or XLSX file with employee data.
        The file will be saved to S3 with current datetime and copied as latest.csv.
        """
        
        current_employee_service = CurrentEmployeeService(config)
        status = current_employee_service.get_last_uploaded_file_status(organization.entity_id)
        if status is None:
            return get_success_response(
                status=None,
                matches=None,
                message="No data"
            )
        
        employee_exclusion_match_service = EmployeeExclusionMatchService(config)
        matches = employee_exclusion_match_service.get_all_matches(organization.entity_id)

        return get_success_response(
            status=status,
            matches=matches,
            message="Exclusion match data retrieved successfully"
        )


@exclusion_match_api.route('/<string:entity_id>')
class EmployeeExclusionMatch(Resource):
    
    @login_required()
    def put(self, person, entity_id):
        """
        Update an exclusion match object with reviewer_notes or status.
        """

        parsed_body = parse_request_body(request, ['reviewer_notes', 'status'])

        reviewer_notes = parsed_body['reviewer_notes']
        status = parsed_body['status']

        if status:
            status = status.lower().strip()
            if status not in ['pending', 'handled']:
                return get_failure_response("Invalid value for status. Must be one of: pending, handled.")

        employee_exclusion_match_service = EmployeeExclusionMatchService(config)
        match = employee_exclusion_match_service.update_exclusion_match(
            entity_id=entity_id,
            reviewer_notes=reviewer_notes,
            reviewer=person,
            status=status
        )
        
        return get_success_response(
            data=match.as_dict()
        )


    @login_required()
    def get(self, person, entity_id):
        """
        Get an exclusion match object by entity_id along with employee and exclusion details.
        """

        employee_exclusion_match_service = EmployeeExclusionMatchService(config)
        current_employee_service = CurrentEmployeeService(config)
        oig_exclusion_service = OigEmployeesExclusionService(config)

        match = employee_exclusion_match_service.get_match_by_entity_id(entity_id)
        employee = current_employee_service.get_employee_by_id(match.employee_id) if match.employee_id else None
        oig_exclusion = oig_exclusion_service.get_exclusion_by_id(match.oig_exclusion_id) if match.oig_exclusion_id else None

        return get_success_response(
            data={
                **match.as_dict(),
                "employee": employee.as_dict() if employee else None,
                "oig_exclusion": oig_exclusion.as_dict() if oig_exclusion else None
            }
        )
