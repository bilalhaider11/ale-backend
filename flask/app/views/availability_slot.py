from flask_restx import Namespace, Resource
from flask import request
from datetime import time, datetime, date, timedelta
from app.helpers.response import get_success_response, get_failure_response, parse_request_body
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.services import EmployeeService, PersonService, AvailabilitySlotService
from common.models import Person, PersonOrganizationRole, Organization, AvailabilitySlot
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
    def post(self, person: Person, roles: list, organization: Organization, employee_id: str):
        """Update or create an availability slot"""
        if PersonOrganizationRoleEnum.EMPLOYEE in roles:
            employee_service = EmployeeService(config)
            employee = employee_service.get_employee_by_id(employee_id, organization.entity_id)
            if employee.person_id != person.entity_id:
                return get_failure_response(message="Unable to perform this action on this employee_id.")

        availability_slot_service = AvailabilitySlotService(config)
        
        parsed_body = parse_request_body(request, [
            'entity_id',
            'day_of_week',
            'start_time',
            'end_time',
            'start_day_of_week',
            'end_day_of_week',
            'start_date',
            'end_date',
            'week_start_date',
            'week_end_date'
        ])

        # Extract fields
        entity_id = parsed_body.pop('entity_id', None)
        day_of_week = parsed_body.pop('day_of_week', None)
        start_time = parsed_body.pop('start_time', None)
        end_time = parsed_body.pop('end_time', None)
        start_date = parsed_body.pop('start_date', None)
        end_date = parsed_body.pop('end_date', None)
        week_start_date = parsed_body.pop('week_start_date', None)
        week_end_date = parsed_body.pop('week_end_date', None)

        # Validate required fields
        if day_of_week is None or not start_time or not end_time:
            raise InputValidationError("day_of_week, start_time or end_time not found in the slot")

        if not isinstance(day_of_week, int) or not (0 <= day_of_week <= 6):
            raise InputValidationError("day_of_week must be an integer between 0 and 6")
        
        # Handle day range fields with defaults
        start_day_of_week = parsed_body.pop('start_day_of_week', day_of_week)
        end_day_of_week = parsed_body.pop('end_day_of_week', day_of_week)

        # Validate day range fields
        for field_name, value in [('start_day_of_week', start_day_of_week), ('end_day_of_week', end_day_of_week)]:
            if not isinstance(value, int) or not (0 <= value <= 6):
                raise InputValidationError(f"{field_name} must be an integer between 0 and 6")
        
        # Validate day range order
        if start_day_of_week > end_day_of_week:
            raise InputValidationError("start_day_of_week cannot be greater than end_day_of_week")
  
        # Parse time strings from "hh:mm" format to datetime.time
        try:                                                                                                                                   
            start_time = datetime.strptime(start_time, '%H:%M').time()                                                                  
            end_time = datetime.strptime(end_time, '%H:%M').time()                                                                           
        except (ValueError, TypeError):                                                                                                              
            raise InputValidationError("start_time and end_time must be in 'hh:mm' format")
    
        start_date = (
            datetime.strptime(start_date, "%Y-%m-%d").date()
            if start_date
            else None
        )

        end_date = (
            datetime.strptime(end_date, "%Y-%m-%d").date()
            if end_date
            else None
        )
        
        if entity_id:
            slot = availability_slot_service.get_availability_slot_by_id(entity_id)
            
            if not slot:
                return get_failure_response("Availability slot not found", status_code=404)
                
            slot.day_of_week = day_of_week
            slot.start_day_of_week = start_day_of_week
            slot.end_day_of_week = end_day_of_week
            slot.start_time = start_time
            slot.end_time = end_time
            slot.employee_id = employee_id
            slot.start_date = start_date
            slot.end_date = end_date
            slot.week_start_date = week_start_date
            slot.week_end_date = week_end_date
    
            slot = availability_slot_service.save_availability_slot(slot)
            message = "Availability slot updated successfully"
        else:
            if week_start_date is None:
                today = datetime.now().date()
                week_start_date = today - timedelta(days=today.weekday())
                if week_start_date.weekday() != 0:
                    raise InputValidationError("week_start_date must be a Monday")

            week_end_date = week_start_date + timedelta(days=6)
            
            slot = AvailabilitySlot(
                day_of_week=day_of_week,
                start_day_of_week=start_day_of_week,
                end_day_of_week=end_day_of_week,
                start_time=start_time,
                end_time=end_time,
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                week_start_date=week_start_date,
                week_end_date=week_end_date
            )

            availability_slot_service.save_availability_slot(slot)
            message = "Availability slot created successfully"
            
        return get_success_response(data=slot, message=message)


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