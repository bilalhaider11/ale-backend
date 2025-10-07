from flask_restx import Namespace, Resource
from flask import request
from datetime import datetime
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.services import EmployeeService, AvailabilitySlotService
from common.models import Person, Organization
from common.app_config import config
from common.helpers.exceptions import InputValidationError, NotFoundError

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

        week_start_date = request.args.get('week_start_date')
        if week_start_date:
            try:
                week_start_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
                if week_start_date.weekday() != 0:
                    return get_failure_response("week_start_date must be a Monday", status_code=400)
            except ValueError:
                return get_failure_response("Invalid week_start_date format. Use YYYY-MM-DD", status_code=400)
            availability_slots = availability_slot_service.get_availability_slots_by_week(employee_id, week_start_date)
        else:
            availability_slots = availability_slot_service.get_availability_slots_by_employee_id(employee_id)
        return get_success_response(data=availability_slots)
    
    @login_required()
    @organization_required(with_roles=[
        PersonOrganizationRoleEnum.EMPLOYEE,
        PersonOrganizationRoleEnum.ADMIN
    ])
    def put(self, person: Person, roles: list, organization: Organization, employee_id: str):
        """Update an existing availability slot"""
        if PersonOrganizationRoleEnum.EMPLOYEE in roles:
            employee_service = EmployeeService(config)
            employee = employee_service.get_employee_by_id(employee_id, organization.entity_id)
            if employee.person_id != person.entity_id:
                return get_failure_response(message="Unable to perform this action on this employee_id.")

        availability_slot_service = AvailabilitySlotService(config)
        
        # Get and validate request data
        slot_data = request.get_json(force=True)
        if not isinstance(slot_data, dict):
            raise InputValidationError("Request body must be a JSON object")
        
        # Validate entity_id is present
        slot_id = slot_data.get('entity_id')
        if not slot_id:
            return get_failure_response("entity_id is required for updating a slot", status_code=400)
        
        try:
            # Update the slot
            updated_slot = availability_slot_service.update_availability_slot(
                employee_id, slot_id, slot_data
            )
            
            return get_success_response(
                message="Availability slot updated successfully",
                data=updated_slot.as_dict()
            )
        except InputValidationError as e:
            return get_failure_response(str(e), status_code=400)
        except NotFoundError as e:
            return get_failure_response(str(e), status_code=404)
        except Exception as e:
            return get_failure_response(f"Error updating availability slot: {str(e)}", status_code=500)


@availability_slot_api.route('')
class MultipleAvailabilitySlotResource(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, organization: Organization):
        availability_slot_service = AvailabilitySlotService(config)
        availability_slots = availability_slot_service.get_availability_slots_for_organization(organization.entity_id)
        return get_success_response(data=availability_slots)


@availability_slot_api.route('/<string:employee_id>', defaults={'slot_id': None})
@availability_slot_api.route('/<string:employee_id>/<string:slot_id>')
class DeleteEmployeeSlotResource(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def delete(self, person, organization, employee_id: str, slot_id: str):
        try:
            series_id = request.args.get("series_id") or None
            from_date = request.args.get("from_date") or None

            availability_slot_service = AvailabilitySlotService(config)

            result = availability_slot_service.delete_employee_availability_slot(
                employee_id=employee_id,
                slot_id=slot_id,
                series_id=series_id,
                from_date=from_date
            )
            return get_success_response(data=result)
        except NotFoundError as e:
            return get_failure_response(str(e), status_code=404)
        except Exception as e:
            return get_failure_response(f"Error deleting employee availability slot: {str(e)}", status_code=500)


@availability_slot_api.route('/create/<string:employee_id>')
class CreateEmployeeSlots(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization, employee_id: str):
        try:
            request_data = request.get_json(force=True)
            availability_slot_service = AvailabilitySlotService(config)
            created_slots = availability_slot_service.expand_and_save_slots(request_data, employee_id)
            return get_success_response(
                count=len(created_slots),
                message='Successfully created the slots for employees.',
            )
        except NotFoundError as e:
            return get_failure_response(str(e), status_code=404)
        except Exception as e:
            return get_failure_response(f"Error creating employee care slots: {str(e)}", status_code=500)