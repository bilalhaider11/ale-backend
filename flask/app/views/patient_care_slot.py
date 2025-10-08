from flask_restx import Namespace, Resource
from flask import request
from datetime import datetime
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.services import PatientService, PatientCareSlotService
from common.models import Person, Organization
from common.app_config import config
from common.helpers.exceptions import InputValidationError, NotFoundError
import uuid

# Create the patient care slot blueprint
patient_care_slot_api = Namespace('patient_care_slot', description="Patient care slot APIs")


@patient_care_slot_api.route('')
class MultipleAvailabilitySlotResource(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, organization: Organization):
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)

        patient_care_slot_service = PatientCareSlotService(config)
        patient_care_slots = patient_care_slot_service.get_patient_care_slots_for_organization(
            organization_id=organization.entity_id,
            start_date=start_date,
            end_date=end_date,
        )
        return get_success_response(data=patient_care_slots)


@patient_care_slot_api.route('/<string:patient_id>')
class PatientCareSlotResource(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person: Person, roles: list, organization: Organization, patient_id: str):
        """Get patient care slots for a specific patient, optionally filtered by week"""
        patient_service = PatientService(config)
        patient_care_slot_service = PatientCareSlotService(config)
        
        # Verify patient belongs to organization
        patient = patient_service.get_patient_by_id(patient_id, organization.entity_id)
        if not patient:
            return get_failure_response("Patient not found in this organization", status_code=404)
        
        # Check if filtering by week
        week_start_date = request.args.get('week_start_date')

        if week_start_date:
            try:
                week_start_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
                if week_start_date.weekday() != 0:
                    return get_failure_response("week_start_date must be a Monday", status_code=400)
            except ValueError:
                return get_failure_response("Invalid week_start_date format. Use YYYY-MM-DD", status_code=400)
            
            # Get slots for specific week
            patient_care_slots = patient_care_slot_service.get_patient_care_slots_by_week(patient_id, week_start_date)
        else:
            # Get all slots for patient
            patient_care_slots = patient_care_slot_service.get_patient_care_slots_by_patient_id(patient_id)
        
        return get_success_response(data=patient_care_slots)
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def put(self, person: Person, organization: Organization, patient_id: str):
        """Update an existing patient care slot"""
        patient_service = PatientService(config)
        patient_care_slot_service = PatientCareSlotService(config)
        
        # Get patient and verify it belongs to organization
        patient = patient_service.get_patient_by_id(patient_id, organization.entity_id)
        if not patient:
            return get_failure_response("Patient not found in this organization", status_code=404)
        
        # Get and validate request data
        slot_data = request.get_json(force=True)
        if not isinstance(slot_data, dict):
            raise InputValidationError("Request body must be a JSON object")
        
        # Validate entity_id is present
        slot_id = slot_data.get('entity_id')
        if not slot_id:
            return get_failure_response("entity_id is required for updating a slot", status_code=400)
        
        try:
            # Update the slot with quota validation
            updated_slot = patient_care_slot_service.update_patient_care_slot(
                patient_id, slot_id, slot_data, patient.weekly_quota
            )
            
            return get_success_response(
                message="Patient care slot updated successfully",
                data=updated_slot.as_dict()
            )
        except InputValidationError as e:
            return get_failure_response(str(e), status_code=400)
        except NotFoundError as e:
            return get_failure_response(str(e), status_code=404)
        except Exception as e:
            return get_failure_response(f"Error updating patient care slot: {str(e)}", status_code=500)


@patient_care_slot_api.route('/<string:patient_id>', defaults={'slot_id': None})
@patient_care_slot_api.route('/<string:patient_id>/<string:slot_id>')
class DeletePatientCareSlotResource(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def delete(self, person, organization, patient_id: str, slot_id: str = None):
        try:
            series_id = request.args.get("series_id") or None
            from_date = request.args.get("from_date") or None

            patient_care_slot_service = PatientCareSlotService(config)

            result = patient_care_slot_service.delete_patient_care_slot(
                patient_id=patient_id,
                slot_id=slot_id,
                series_id=series_id,
                from_date=from_date
            )
            return get_success_response(data=result)

        except NotFoundError as e:
            return get_failure_response(str(e), status_code=404)
        except Exception as e:
            return get_failure_response(
                f"Error deleting patient care slot: {str(e)}", status_code=500
            )


@patient_care_slot_api.route('/create/<string:patient_id>')
class CreatePatientSlots(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization, patient_id: str):
        try:
            request_data = request.get_json(force=True)

            if not isinstance(request_data, dict):
                raise InputValidationError("Request body must be a JSON object")

            assigned_employee_id = request_data.get('assigned_employee_id')

            clean_request_data = {k: v for k, v in request_data.items() if k not in ['assigned_employee_id', 'visit_date']}

            patient_care_slot_service = PatientCareSlotService(config)
            created_slots = patient_care_slot_service.expand_and_save_slots(clean_request_data, patient_id)

            care_visits = []

            if assigned_employee_id and created_slots:
                from common.services import CareVisitService
                from datetime import datetime, timedelta
                from common.services import AvailabilitySlotService
                availability_slot_service = AvailabilitySlotService(config)
                care_visit_service = CareVisitService(config)

                series_id = uuid.uuid4().hex if len(created_slots) > 1 else None
                for slot in created_slots:
                    employee_logical_key = availability_slot_service.has_availability_for_slot(
                        employee_id=assigned_employee_id,
                        day_of_week=slot.day_of_week,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        start_date=slot.start_date,
                        match_type="contains"
                    )

                    if not employee_logical_key:
                        availability_slot_data = {
                            "day_of_week": slot.day_of_week,
                            "start_day_of_week": slot.start_day_of_week,
                            "end_day_of_week": slot.end_day_of_week,
                            "start_time": slot.start_time,
                            "end_time": slot.end_time,
                            "employee_id": assigned_employee_id,
                            "series_id": series_id,
                            "week_start_date": slot.week_start_date,
                            "week_end_date": slot.week_end_date,
                            "start_date": slot.start_date,
                            "end_date": slot.end_date
                        }
                        employee_slot = availability_slot_service.create_availability_slot(availability_slot_data)
                        employee_logical_key = employee_slot.logical_key

                    visit_data = {
                        'patient_id': patient_id,
                        'employee_id': assigned_employee_id,
                        'visit_date': slot.start_date.strftime('%Y-%m-%d'),
                        'scheduled_start_time': slot.start_time.strftime('%H:%M'),
                        'scheduled_end_time': slot.end_time.strftime('%H:%M'),
                        'care_slot_logical_key': slot.logical_key,
                        'employee_logical_key': employee_logical_key,
                        'scheduled_by_id': person.entity_id,
                        'organization_id': organization.entity_id
                    }
                    care_visit = care_visit_service.create_care_visit_from_assignment(visit_data)
                    care_visits.append(care_visit.as_dict())

            message = f'Successfully created {len(created_slots)} care slots'

            if care_visits:
                message += f' and {len(care_visits)} employee assignments'

            return get_success_response(
                count=len(created_slots),
                message=message,
            )

        except NotFoundError as e:
            return get_failure_response(str(e), status_code=404)
        except Exception as e:
            return get_failure_response(f"Error creating patient care slots: {str(e)}", status_code=500)