import tempfile
import os
from flask import request
from flask_restx import Resource, Namespace
from common.app_config import config
from common.app_logger import create_logger
from datetime import datetime, timedelta
from app.helpers.decorators import login_required, organization_required
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields

from common.models.patient_care_slot import PatientCareSlot
from common.models import Person, Patient
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.services.person import PersonService
from common.services.patient import PatientService
from common.services.patient_care_slot import PatientCareSlotService

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
        
        parsed_body = parse_request_body(request, [
            'entity_id',
            'first_name',
            'last_name',
            'date_of_birth',
            'social_security_number',
            'care_period_start',
            'care_period_end',
            'weekly_quota',
        ])

        entity_id = parsed_body.pop('entity_id', None)
        first_name = parsed_body.pop('first_name', None)
        last_name = parsed_body.pop('last_name', None)
        date_of_birth = parsed_body.pop('date_of_birth', None)
        social_security_number = parsed_body.pop('social_security_number', None)
        care_period_start = parsed_body.pop('care_period_start', None)
        care_period_end = parsed_body.pop('care_period_end', None)
        weekly_quota = parsed_body.pop('weekly_quota', None)

        validate_required_fields(parsed_body)
        
        if entity_id:
            patient = patient_service.get_patient_by_id(entity_id, organization.entity_id)
            if not patient:
                return get_failure_response("Patient not found", status_code=404)
            
            patient.date_of_birth = date_of_birth
            patient.social_security_number = social_security_number
            patient.care_period_start = care_period_start
            patient.care_period_end = care_period_end
            patient.weekly_quota = weekly_quota

            if patient.person_id:
                person_obj = person_service.get_person_by_id(patient.person_id)
                if person_obj and (person_obj.first_name != first_name or person_obj.last_name != last_name):
                    person_obj.first_name = first_name
                    person_obj.last_name = last_name
                    person_service.save_person(person_obj)
            else:
                person_obj = Person(
                    first_name=first_name,
                    last_name=last_name,
                )
                person_obj = person_service.save_person(person_obj)
                patient.person_id = person_obj.entity_id

            patient.changed_by_id = person.entity_id
            patient = patient_service.save_patient(patient)
            action = "updated"
        else:
            person_obj = Person(
                first_name=first_name,
                last_name=last_name
            )
            person_obj = person_service.save_person(person_obj)
            
            patient = Patient(
                date_of_birth=date_of_birth,
                social_security_number=social_security_number,
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

@patient_api.route('/<string:patient_id>/slots')
class PatientCareSlots(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization, patient_id):
        """Get patient care slots"""
        patient_service = PatientService(config)
        patient_care_slot_service = PatientCareSlotService(config)

        patient = patient_service.get_patient_by_id(patient_id, organization.entity_id)
        
        if not patient or patient.organization_id != organization.entity_id:
            return get_failure_response("Patient not found in this organization", status_code=404)
        
        week_start_date = request.args.get('week_start_date')
        
        if week_start_date:
            try:
                week_start_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
                if week_start_date.weekday() != 0:
                    return get_failure_response(message="week_start_date must be a Monday", status_code=400)
            except ValueError:
                return get_failure_response(message="Invalid week_start_date format", status_code=400)
        
        if week_start_date:
            current_week_slots = patient_care_slot_service.get_patient_care_slots_by_week(patient_id, week_start_date)
        else:
            current_week_slots = {}
        
        return get_success_response(data=current_week_slots)
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization, patient_id):
        """Update care slots for a patient for a specific week"""
        patient_service = PatientService(config)
        patient_care_slot_service = PatientCareSlotService(config)
        
        parsed_body = parse_request_body(request, [
            'week_start_date',
            'week_end_date',
            'selected_days',
            'consistent_slots',
            'day_specific_slots'
        ])
        
        week_start_date = parsed_body.get('week_start_date')
        week_end_date = parsed_body.get('week_end_date')

        validate_required_fields({'week_start_date': week_start_date})
        
        patient = patient_service.get_patient_by_id(patient_id, organization.entity_id)
        if not patient:
            return get_failure_response("Patient not found in this organization", status_code=404)
        
        try:
            week_start_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
        except ValueError:
            return get_failure_response("week_start_date must be in 'YYYY-MM-DD' format", status_code=400)
        
        if week_start_date.weekday() != 0:
            return get_failure_response("week_start_date must be a Monday", status_code=400)
        
        if not week_end_date:
            week_end_date = week_start_date + timedelta(days=6)
        else:
            try:
                week_end_date = datetime.strptime(week_end_date, '%Y-%m-%d').date()
                if week_end_date != week_start_date + timedelta(days=6):
                    return get_failure_response("week_end_date must be exactly 6 days after week_start_date", status_code=400)
            except ValueError:
                return get_failure_response("week_end_date must be in 'YYYY-MM-DD' format", status_code=400)
        
        slots = []
        
        selected_days = parsed_body.get('selected_days', [])
        consistent_slots_data = parsed_body.get('consistent_slots', [])
        
        if selected_days and consistent_slots_data:
            for day in selected_days:
                if not isinstance(day, int) or day < 0 or day > 6:
                    return get_failure_response("selected_days must contain integers between 0 and 6", status_code=400)
            
            consistent_slots = []
            for slot_data in consistent_slots_data:
                try:
                    start_time = datetime.strptime(slot_data['start_time'], '%H:%M').time()
                    end_time = datetime.strptime(slot_data['end_time'], '%H:%M').time()
                    consistent_slots.append({
                        'start_time': start_time,
                        'end_time': end_time
                    })
                except (ValueError, TypeError, KeyError):
                    return get_failure_response("consistent_slots must have start_time and end_time in 'HH:MM' format", status_code=400)
            
            slots.extend(patient_care_slot_service.apply_consistent_slots_to_days(
                patient_id, selected_days, consistent_slots, week_start_date, week_end_date
            ))
        
        day_specific_slots = parsed_body.get('day_specific_slots', {})
        for day_str, day_slots in day_specific_slots.items():
            try:
                day = int(day_str)
                for slot_data in day_slots:
                    start_time = datetime.strptime(slot_data['start_time'], '%H:%M').time()
                    end_time = datetime.strptime(slot_data['end_time'], '%H:%M').time()
                    
                    slot = PatientCareSlot(
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time,
                        week_start_date=week_start_date,
                        week_end_date=week_end_date,
                        is_consistent_slot=False
                    )
                    slots.append(slot)
            except (ValueError, TypeError, KeyError):
                return get_failure_response("Error processing day_specific_slots. Format should be day: [{start_time, end_time}]", status_code=400)
        
        total_hours = 0
        for slot in slots:
            if slot.start_time and slot.end_time:
                start_minutes = slot.start_time.hour * 60 + slot.start_time.minute
                end_minutes = slot.end_time.hour * 60 + slot.end_time.minute
                total_hours += (end_minutes - start_minutes) / 60
        
        if patient.weekly_quota is not None and total_hours > patient.weekly_quota:
            return get_failure_response(
                f"Weekly quota exceeded: attempted {total_hours:.2f} h "
                    f"(limit {patient.weekly_quota} h).",
                status_code=400
            )
            
        updated_slots = patient_care_slot_service.upsert_patient_care_slots(
            patient_id, 
            slots,
            week_start_date=week_start_date,
            week_end_date=week_end_date
        )
        
        current_week_slots = patient_care_slot_service.get_patient_care_slots_by_week(patient_id, week_start_date)
        care_duration = patient_care_slot_service.calculate_total_weekly_duration(patient_id, week_start_date)
        
        care_requirements_saved = len(updated_slots) > 0
        
        return get_success_response(
            message="Patient care slots updated successfully",
            data={
                'slots': current_week_slots,
                'care_requirements_saved': care_requirements_saved,
                'care_duration': care_duration,
                'slots_count': len(updated_slots)
            }
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
