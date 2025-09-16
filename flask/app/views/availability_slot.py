from flask_restx import Namespace, Resource
from flask import request
from datetime import time, datetime
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.services import EmployeeService, PersonService, AvailabilitySlotService
from common.models import Person, PersonOrganizationRole, Organization, AvailabilitySlot
from common.app_config import config
from common.helpers.exceptions import InputValidationError

# Create the organization blueprint
availability_slot_api = Namespace('availability_slot', description="Person-related APIs")


@availability_slot_api.route('/<string:employee_id>')
class AvailabilitySlotResource(Resource):

    @login_required()
    @organization_required(with_roles=[
        PersonOrganizationRoleEnum.EMPLOYEE,
        PersonOrganizationRoleEnum.ADMIN
    ])
    def get(self, person: Person, roles: list, organization: Organization, employee_id: str):

        if PersonOrganizationRoleEnum.EMPLOYEE in roles:
            employee_service = EmployeeService(config)
            employee = employee_service.get_employee_by_id(employee_id, organization.entity_id)
            if employee.person_id != person.entity_id:
                return get_failure_response(message="Unable to perform this action on this employee_id.")

        availability_slot_service = AvailabilitySlotService(config)
        availability_slots = availability_slot_service.get_availability_slots_by_employee_id(employee_id)
        return get_success_response(data=availability_slots)

    @login_required()
    @organization_required(with_roles=[
        PersonOrganizationRoleEnum.EMPLOYEE,
        PersonOrganizationRoleEnum.ADMIN
    ])
    def post(self, person: Person, roles: list, organization: Organization, employee_id: str):

        if PersonOrganizationRoleEnum.EMPLOYEE in roles:
            employee_service = EmployeeService(config)
            employee = employee_service.get_employee_by_id(employee_id, organization.entity_id)
            if employee.person_id != person.entity_id:
                return get_failure_response(message="Unable to perform this action on this employee_id.")

        request_json = request.get_json(force=True)
        if type(request_json) is not list:
            raise InputValidationError("A list of slots is required")
        
        slots = []
        for slot in request_json:
            if type(slot) is not dict:
                raise InputValidationError("A list of slot objects is required.")
            
            # validate slots
            required_fields = ["day_of_week", "start_time", "end_time"]
            if not all(field in slot for field in required_fields):
                raise InputValidationError("day_of_week, start_time or end_time not found in the slot")
            
            # Parse time strings from "hh:mm" format to datetime.time
            try:                                                                                                                                         
                start_time = datetime.strptime(slot['start_time'], '%H:%M').time()                                                                       
                end_time = datetime.strptime(slot['end_time'], '%H:%M').time()                                                                           
            except (ValueError, TypeError):                                                                                                              
                raise InputValidationError("start_time and end_time must be in 'hh:mm' format")

            slot = AvailabilitySlot(
                day_of_week=slot['day_of_week'],
                start_time=start_time,
                end_time=end_time
            )
            slots.append(slot)

        availability_slot_service = AvailabilitySlotService(config)
        availability_slots = availability_slot_service.upsert_availability_slots(employee_id, slots)
        return get_success_response(data=availability_slots)


@availability_slot_api.route('')
class MultipleAvailabilitySlotResource(Resource):

    @login_required()
    @organization_required(with_roles=[
        PersonOrganizationRoleEnum.EMPLOYEE,
        PersonOrganizationRoleEnum.ADMIN
    ])
    def get(self, person: Person, role: PersonOrganizationRole, organization: Organization):
        availability_slot_service = AvailabilitySlotService(config)
        availability_slots = availability_slot_service.get_availability_slots_for_organization(organization.entity_id)
        return get_success_response(data=availability_slots)
