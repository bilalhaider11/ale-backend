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


@patient_care_slot_api.route('/<string:patient_id>')
class PatientCareSlotResource(Resource):

    @login_required()
    @organization_required(with_roles=[
        PersonOrganizationRoleEnum.ADMIN
    ])
    def get(self, person: Person, roles: list, organization: Organization, patient_id: str):
        patient_care_slot_service = PatientCareSlotService(config)
        patient_care_slots = patient_care_slot_service.get_patient_care_slots_by_patient_id(patient_id)
        return get_success_response(data=patient_care_slots)
