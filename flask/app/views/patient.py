import tempfile
import os
from flask import request, jsonify
from flask_restx import Resource, Namespace
from common.app_config import config
from common.app_logger import create_logger
from common.services.patient import PatientService
from common.models.person_organization_role import PersonOrganizationRoleEnum

from app.helpers.decorators import login_required, organization_required
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields

logger = create_logger()

patient_api = Namespace('patient', description='Patient management endpoints')
@patient_api.route('/admin')
class PatientList(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """
        Get all patients for the organization.
        """
        patient_service = PatientService(config)
        patients = patient_service.get_all_patients_for_organization(organization.entity_id)
        
        return get_success_response(
            patients=patients,
            count=len(patients)
        )
        # return get_success_response(
        #     patients=[patient.as_dict() for patient in patients],
        #     count=len(patients)
        # )

@patient_api.route('/upload')
class PatientFileUpload(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Upload a CSV or XLSX file with patient data.
        """
        # Check if file is provided
        if 'file' not in request.files:
            return get_failure_response("No file provided", 400)

        file = request.files['file']
        file_id = request.form.get('file_id', None)
        
        # Check if file is empty
        if file.filename == '':
            return get_failure_response("No file selected", 400)
        
        # Check file extension
        allowed_extensions = {'.csv', '.xlsx'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            return get_failure_response("File type not supported. Please upload a CSV or XLSX file.", 400)
        
        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)
        
        try:
            # Process and upload the file
            patient_service = PatientService(config, person.entity_id)
            result = patient_service.upload_patient_list(
                organization_id=organization.entity_id,
                person_id=person.entity_id,
                file_path=temp_path,
                original_filename=file.filename,
                file_id=file_id,
            )
        
            return get_success_response(
                message=f"File uploaded successfully",
                upload_info=result,
            )
        
        except Exception as e:
            logger.error(f"Error processing patient file: {str(e)}")
            return get_failure_response(f"Error processing file: {str(e)}", 500)
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


@patient_api.route('')
class PatientCreate(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Create a single patient record.
        """
        # Get JSON data from request
        data = request.get_json()
        
        parsed_body = parse_request_body(request, ['first_name', 'last_name', 'date_of_birth', 'social_security_number'])
        validate_required_fields(parsed_body)
        
        try:
            patient_service = PatientService(config, person.entity_id)
            
            # Create patient using the service
            created_patient = patient_service.create_single_patient(
                organization_id=organization.entity_id,
                user_id=person.entity_id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                date_of_birth=data['date_of_birth'],
                ssn=data['social_security_number'] 
            )
            
            return get_success_response(
                message="Patient created successfully",
                patient=created_patient.as_dict(convert_datetime_to_iso_string=True, convert_uuids=True)
            )
            
        except Exception as e:
            return get_failure_response(f"Error creating patient: {str(e)}", 500)


