import os
import tempfile
from flask import request
from flask_restx import Namespace, Resource

from common.app_config import config
from common.services.employee import EmployeeService
from common.services.current_employees_file import CurrentEmployeesFileService
from common.services.employee_exclusion_match import EmployeeExclusionMatchService
from common.services.oig_employees_exclusion import OigEmployeesExclusionService
from common.services.s3_client import S3ClientService
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.models.current_employees_file import CurrentEmployeesFileStatusEnum
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
        employee_service = EmployeeService(config)
        current_employee_count = employee_service.get_employees_count(organization_id=organization.entity_id)

        employee_exclusion_match_service = EmployeeExclusionMatchService(config)
        matches_count = employee_exclusion_match_service.get_all_matches_count(organization.entity_id)

        current_employees_file_service = CurrentEmployeesFileService(config)
        files_count = current_employees_file_service.get_files_count(
            organization.entity_id, status=CurrentEmployeesFileStatusEnum.DONE
        )

        return get_success_response(
            current_employee_count=current_employee_count,
            matches_count=matches_count,
            files_count=files_count,
            message="Exclusion match data retrieved successfully"
        )


@exclusion_match_api.route('')
class EmployeeExclusionMatch(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """
        Get all exclusion match objects for the organization.
        """
        
        employee_exclusion_match_service = EmployeeExclusionMatchService(config)
        matches = employee_exclusion_match_service.get_all_matches(organization.entity_id)

        return get_success_response(
            data=matches,
            message="Exclusion match data retrieved successfully"
        )

@exclusion_match_api.route('/employee/<string:employee_id>')
class EmployeeExclusionMatchRecordByEmployee(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization, employee_id):
        """
        Get exclusion match records for a specific employee.
        """
        
        employee_exclusion_match_service = EmployeeExclusionMatchService(config)
        matches = employee_exclusion_match_service.get_matches_by_employee_id(
            organization_id=organization.entity_id,
            employee_id=employee_id
        )

        return get_success_response(
            data=matches,
            message="Exclusion match records retrieved successfully"
        )

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def put(self, person, organization, employee_id):
        """
        Update an exclusion match object with reviewer_notes or status by employee_id.
        """

        parsed_body = parse_request_body(request, ['reviewer_notes', 'status'])

        reviewer_notes = parsed_body['reviewer_notes']
        status = parsed_body['status']

        if status:
            status = status.lower().strip()
            if status not in ['pending', 'handled']:
                return get_failure_response("Invalid value for status. Must be one of: pending, handled.")

        employee_exclusion_match_service = EmployeeExclusionMatchService(config)
        employee_exclusion_match_service.update_exclusion_match(
            matched_entity_type="employee",
            matched_entity_id=employee_id,
            organization_id=organization.entity_id,
            reviewer_notes=reviewer_notes,
            reviewer=person,
            status=status
        )

        return get_success_response(
            message="Matches updated successfully",
        )


@exclusion_match_api.route('/s3-image')
class ExclusionMatchS3Image(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """
        Get a presigned URL for an S3 image associated with exclusion match verification.
        """
        s3_key = request.args.get('s3_key')
        if not s3_key:
            return get_failure_response("S3 key is required")
        
        try:
            s3_client = S3ClientService()
            # Generate presigned URL with 1 hour expiration
            presigned_url = s3_client.generate_presigned_url(s3_key, expiration=3600)
            
            return get_success_response(
                data={"url": presigned_url},
                message="Presigned URL generated successfully"
            )
        except Exception as e:
            return get_failure_response(f"Failed to generate presigned URL: {str(e)}")
