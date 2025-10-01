from flask_restx import Namespace, Resource
from flask import request
from datetime import time, datetime
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.services import EmployeeService, PersonService, AvailabilitySlotService, PatientService, PatientCareSlotService
from common.models import Person, PersonOrganizationRole, Organization, AvailabilitySlot
from common.app_config import config
from common.helpers.exceptions import InputValidationError

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
    def post(self, person: Person, organization: Organization, patient_id: str):
        """Create a new patient care slot"""
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
        
        try:
            # Create the slot with quota validation
            created_slot = patient_care_slot_service.create_patient_care_slot(
                patient_id, slot_data, patient.weekly_quota
            )
            
            return get_success_response(
                message="Patient care slot created successfully",
                data=created_slot.as_dict()
            )
        except InputValidationError as e:
            return get_failure_response(str(e), status_code=400)
        except Exception as e:
            return get_failure_response(f"Error creating patient care slot: {str(e)}", status_code=500)
    
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
        except Exception as e:
            return get_failure_response(f"Error updating patient care slot: {str(e)}", status_code=500)


@patient_care_slot_api.route('/<string:patient_id>/<string:slot_id>')
class DeletePatientCareSlotResource(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def delete(self, person, organization, patient_id: str, slot_id: str):
        patient_care_slot_service = PatientCareSlotService(config)
        care_slot = patient_care_slot_service.delete_patient_care_slot(patient_id=patient_id, slot_id=slot_id)
        return get_success_response(data=care_slot)
