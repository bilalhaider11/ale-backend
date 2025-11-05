import tempfile
import os
import csv
from openpyxl import load_workbook
from common.models.alert import AlertLevelEnum, AlertStatusEnum
from flask import request
from flask_restx import Resource, Namespace
from common.app_config import config
from common.app_logger import create_logger
from datetime import datetime, timedelta, date
from app.helpers.decorators import login_required, organization_required
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from common.models.alert import AlertLevelEnum, AlertStatusEnum

from common.models import Person, Patient
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.services.person import PersonService
from common.services.patient import PatientService
from common.services.patient_care_slot import PatientCareSlotService
from common.services.organization import OrganizationService
from common.services.alert import AlertService
logger = create_logger()

patient_api = Namespace('patient', description='Patient management endpoints')


@patient_api.route('/admin')
class PatientList(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """Get all patients for the organization"""
        patient_service = PatientService(config)
        patients = patient_service.get_all_patients_for_organization(organization.entity_id)
        
        return get_success_response(
            patients=patients,
            count=len(patients)
        )

@patient_api.route('/admin/<string:entity_id>')
class PatientDetails(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization, entity_id):
        """Get a single patient by their entity_id."""
        patient_service = PatientService(config)
        patient = patient_service.get_patient_by_id(entity_id, organization.entity_id)

        if not patient:
            return get_failure_response("Patient not found", status_code=404)

        return get_success_response(
            message="Patient retrieved successfully",
            data=patient.as_dict()
        )
        
        

@patient_api.route('/upload')
class PatientFileUpload(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """Upload a CSV or XLSX file with patient data"""
        if 'file' not in request.files:
            return get_failure_response("No file provided", 400)

        file = request.files['file']
        file_id = request.form.get('file_id', None)
        
        if file.filename == '':
            return get_failure_response("No file selected", 400)
        
        allowed_extensions = {'.csv', '.xlsx'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            return get_failure_response("File type not supported. Please upload a CSV or XLSX file.", 400)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)
        
        try:
            patient_service = PatientService(config, person.entity_id)
            result = patient_service.upload_patient_list(
                organization_id=organization.entity_id,
                person_id=person.entity_id,
                file_path=temp_path,
                original_filename=file.filename,
                file_id=file_id,
            )
            
            print("final result from views of patient: ",result)
        
            return get_success_response(
                message="File uploaded successfully",
                upload_info=result,
            )
        
        except Exception as e:
            logger.error(f"Error processing patient file: {str(e)}")
            return get_failure_response(f"Error processing file: {str(e)}", 500)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

@patient_api.route('')
class PatientResource(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """Update or create a patient record"""
        patient_service = PatientService(config)
        person_service = PersonService(config)
        alert_service = AlertService(config)
        organization_service = OrganizationService(config)
        
        
        parsed_body = parse_request_body(request, [
            'entity_id',
            'first_name',
            'last_name',
            'date_of_birth',
            'medical_record_number',
            'gender',
            'care_period_start',
            'care_period_end',
            'weekly_quota',
        ])

        entity_id = parsed_body.pop('entity_id', None)
        first_name = parsed_body.pop('first_name', None)
        last_name = parsed_body.pop('last_name', None)
        date_of_birth = parsed_body.pop('date_of_birth', None)
        gender = parsed_body.pop('gender', None)
        medical_record_number = parsed_body.pop('medical_record_number', None)
        care_period_start = parsed_body.pop('care_period_start', None)
        care_period_end = parsed_body.pop('care_period_end', None)
        weekly_quota = parsed_body.pop('weekly_quota', None)

        validate_required_fields(parsed_body)
        
        if not medical_record_number:
            MRN_auto_assigner = organization_service.get_next_patient_MRN(organization.entity_id)
            medical_record_number = MRN_auto_assigner
            
        existing_patient = patient_service.patient_repo.get_by_patient_mrn(medical_record_number, organization.entity_id)
        
        print("existing patient: ",existing_patient)
        #logic for duplicate patient
        if existing_patient:
            print("duplicates")
            description = f"Duplicate employee ID detected: Duplicate patient detected: ${medical_record_number} for organization ${organization.entity_id}.${medical_record_number} for organization ${organization.entity_id}."
            status_ =  AlertStatusEnum.ADDRESSED.value
            level = AlertLevelEnum.WARNING.value
            title = 'Patient'
            logger.warning(
                f"Duplicate detected: {medical_record_number} for organization {organization.entity_id}. "
                f"Existing employee: {existing_patient.entity_id} . "
                f"Creating new employee anyway as per requirements."
                
            )
            
            alert_service = AlertService(config)
            try:
                print(alert_service)
                create_duplicateRecord_alert = alert_service.create_alert(
                    organization_id = organization.entity_id,
                    title = title,
                    description = description,
                    alert_type = level,
                    status = status_,
                    assigned_to_id = medical_record_number
                
                )
            except Exception as e:
                logger.error(f"Error processing patient file: {str(e)}")
            
 #####################################################################################       
        if entity_id:
            patient = patient_service.get_patient_by_id(entity_id, organization.entity_id)
            
            
            if not patient:
                return get_failure_response("Patient not found", status_code=404)
            
            patient.medical_record_number = medical_record_number
            patient.care_period_start = care_period_start
            patient.care_period_end = care_period_end
            patient.weekly_quota = weekly_quota

            if patient.person_id:
                person_obj = person_service.get_person_by_id(patient.person_id)
                if person_obj and (
                    person_obj.first_name != first_name 
                    or person_obj.last_name != last_name
                    or person_obj.date_of_birth != date_of_birth
                    or person_obj.gender != gender
                ):
                    person_obj.first_name = first_name
                    person_obj.last_name = last_name
                    person_obj.date_of_birth = date_of_birth
                    person_obj.gender = gender
                    person_service.save_person(person_obj)
            else:
                person_obj = Person(
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=date_of_birth,
                    gender=gender
                )
                person_obj = person_service.save_person(person_obj)
                patient.person_id = person_obj.entity_id

            patient.changed_by_id = person.entity_id
            patient = patient_service.save_patient(patient)
            action = "updated"
        else:
            person_obj = Person(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=gender
            )
            person_obj = person_service.save_person(person_obj)
            
            patient = Patient(
                medical_record_number=medical_record_number,
                care_period_start=care_period_start,
                care_period_end=care_period_end,
                weekly_quota=weekly_quota,
                organization_id=organization.entity_id,
                person_id=person_obj.entity_id,
                changed_by_id=person.entity_id
            )
            
            patient = patient_service.save_patient(patient)
            action = "created"
        
        return get_success_response(
            message=f"Patient {action} successfully",
            data=patient.as_dict()
        )

@patient_api.route('/by/slot')
class PatientsBySlot(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """
        Get all patients for the organization.
        """

        date = request.args['date']
        slot_start_time = request.args['start_time']
        slot_end_time = request.args['end_time']
        employee_id = request.args['employee_id']

        # Parse date and time strings
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
            slot_start_time = datetime.strptime(slot_start_time, '%H:%M').time()
            slot_end_time = datetime.strptime(slot_end_time, '%H:%M').time()
        except ValueError:
            return get_failure_response("Invalid date or time format", status_code=400)

        patient_care_slot_service = PatientCareSlotService(config)
        patient_care_slots = patient_care_slot_service.get_patient_care_slots_for_time_slot(
            start_time=slot_start_time,
            end_time=slot_end_time,
            visit_date=date,
            employee_id=employee_id,
            organization_ids=[organization.entity_id]
        )

        return get_success_response(
            slots=patient_care_slots,
            count=len(patient_care_slots)
        )
