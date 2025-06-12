import os
import tempfile
from flask import request
from flask_restx import Namespace, Resource

from common.app_config import config
from common.services.employee import EmployeeService
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required

employee_api = Namespace('employee', description='Employee operations')


@employee_api.route('/upload-csv')
class EmployeeCSVUpload(Resource):
    
    @login_required()
    def post(self, person):
        """
        Upload a CSV file with employee data.
        The file will be saved to S3 with current datetime and copied as latest.csv.
        """
        if 'file' not in request.files:
            return get_failure_response("No csv file provided", status_code=400)
        
        file = request.files['file']
        
        if not file.filename:
            return get_failure_response("No file selected", status_code=400)
        
        # Check if file is a CSV
        if not file.filename.lower().endswith('.csv'):
            return get_failure_response("File must be a CSV", status_code=400)
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Upload file to S3
            employee_service = EmployeeService()
            upload_result = employee_service.upload_employee_csv(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return get_success_response(
                message="CSV file uploaded successfully",
                upload_info=upload_result
            )
            
        except Exception as e:
            # Clean up temporary file in case of error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            return get_failure_response(
                f"Error uploading file: {str(e)}",
                status_code=500
            )
