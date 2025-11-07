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

# Create the patient care slot blueprint
patient_care_slot_api = Namespace('patient_care_slot', description="Patient care slot APIs")


@patient_care_slot_api.route('')
class MultipleAvailabilitySlotResource(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, organization: Organization):
        patient_care_slot_service = PatientCareSlotService(config)
        patient_care_slots = patient_care_slot_service.get_patient_care_slots_for_organization(organization.entity_id)
        return get_success_response(data=patient_care_slots)


@patient_care_slot_api.route('/<string:patient_id>')
class PatientCareSlotResource(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person: Person, roles: list, organization: Organization, patient_id: str):
        """Get patient care slots for a specific patient"""
        patient_service = PatientService(config)
        patient_care_slot_service = PatientCareSlotService(config)
        
        # Verify patient belongs to organization
        patient = patient_service.get_patient_by_id(patient_id, organization.entity_id)
        if not patient:
            return get_failure_response("Patient not found in this organization", status_code=404)
        
        # Check for date range filtering
        start_date = request.args.get('start_date')
        
        if start_date:
            
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            patient_care_slots = patient_care_slot_service.get_patient_care_slots_by_week(patient_id, start_date)
            
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
                from common.services import CareVisitService,AvailabilitySlotService
                from datetime import datetime, timedelta
                
                
                care_visit_service = CareVisitService(config)
                availability_slot_service = AvailabilitySlotService(config)
                
                
                created_availability_slots = availability_slot_service.expand_and_save_slots(request_data, assigned_employee_id)
                
                for slot, avail_slot in zip(created_slots, created_availability_slots):
                    visit_data = {
                        'patient_id': patient_id,
                        'employee_id': assigned_employee_id,
                        'visit_date': slot.start_date.strftime('%Y-%m-%d'),
                        'scheduled_start_time': slot.start_time.strftime('%H:%M'),
                        'scheduled_end_time': slot.end_time.strftime('%H:%M'),
                        'patient_care_slot_id': slot.entity_id,
                        'availability_slot_id': avail_slot.entity_id,
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