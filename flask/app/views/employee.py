import os
import tempfile
from flask import request
from flask_restx import Namespace, Resource

from common.app_config import config
from common.app_logger import logger
from common.services.employee import EmployeeService
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum

employee_api = Namespace('employee', description='Employee operations')


@employee_api.route('/upload')
class EmployeeListUpload(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Upload a CSV or XLSX file with employee or caregiver data.
        The file will be saved to S3 with current datetime and copied as latest.csv.
        """
        if 'file' not in request.files:
            return get_failure_response("No file provided", status_code=400)
        
        file = request.files['file']
        file_id = request.form.get('file_id', None)
        
        if not file.filename:
            return get_failure_response("No file selected", status_code=400)
        
        # Check if file is a CSV or XLSX
        allowed_extensions = ['.csv', '.xlsx']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return get_failure_response("File must be a CSV or XLSX", status_code=400)
        
        # Save file temporarily with appropriate extension
        file_extension = '.csv' if file.filename.lower().endswith('.csv') else '.xlsx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        try:
            # Upload file to S3
            employee_service = EmployeeService(config)
            upload_result = employee_service.upload_employee_list(organization.entity_id, person.entity_id, temp_file_path, original_filename=file.filename, file_id=file_id)

            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return get_success_response(
                message="File uploaded successfully",
                upload_info=upload_result
            )

        except Exception as e:
            # Clean up temporary file in case of error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            logger.exception(e)
            return get_failure_response(
                f"Error uploading file: {str(e)}",
                status_code=500
            )
