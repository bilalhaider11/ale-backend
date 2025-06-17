import os
import tempfile
from flask import request
from flask_restx import Namespace, Resource

from common.app_config import config
from common.services.current_employee import CurrentEmployeeService
from common.services.employee_exclusion_match import EmployeeExclusionMatchService
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required

exclusion_match_api = Namespace('exclusion_match', description='Exclusion match operations')


@exclusion_match_api.route('/status')
class EmployeeExclusionMatch(Resource):
    
    @login_required()
    def get(self, person):
        """
        Upload a CSV or XLSX file with employee data.
        The file will be saved to S3 with current datetime and copied as latest.csv.
        """
        
        current_employee_service = CurrentEmployeeService(config)
        status = current_employee_service.get_last_uploaded_file_status()
        if status is None:
            return get_success_response(
                status=None,
                matches=None,
                message="No data"
            )
        
        if status.get("status") != "done":
            matches = None
        else:
            employee_exclusion_match_service = EmployeeExclusionMatchService(config)
            matches = employee_exclusion_match_service.get_all_matches()

        return get_success_response(
            status=status,
            matches=matches,
            message="Exclusion match data retrieved successfully"
        )
