import re
import base64
from flask_restx import Namespace, Resource
from flask import request
from datetime import datetime
from werkzeug.datastructures import FileStorage
from app.helpers.response import (
    get_success_response,
    get_failure_response,
    parse_request_body,
    validate_required_fields,
)
from common.app_config import config
from common.services import (
    OrganizationService,
    CareVisitService,
    PatientCareSlotService,
    PersonOrganizationInvitationService,
    PersonOrganizationRoleService,
    PersonService,
    EmailService,
    EmployeeService,
    PatientService
)

from common.models import Organization
from common.models import PersonOrganizationRoleEnum, Person, CareVisitStatusEnum, PatientCareSlot
from app.helpers.decorators import (login_required,
                                    organization_required,
                                    has_role
                                    )
from common.helpers.exceptions import APIException

# Create the care visits blueprint
care_visit_api = Namespace('care_visit', description="Care Visit-related APIs")


def _validate_visit_data(visit_data: dict, required_fields: list):
    """Helper function to validate individual visit data"""
    for field in required_fields:
        if field not in visit_data or not visit_data[field] or not str(visit_data[field]).strip():
            raise ValueError(f"'{field}' is required and cannot be empty in visit data.")


def _process_visit_payload(request_data, patient_id=None, employee_id=None):
    """
    Process visit payload - handles both single object and array formats.
    Returns a list of visit data dictionaries.
    """
    required_fields = [
        'visit_date', 'scheduled_start_time',
        'scheduled_end_time', 'availability_slot_id', 'patient_care_slot_id'
    ]

    # Add the missing ID field to required fields
    if patient_id is None:
        required_fields.append('patient_id')
    if employee_id is None:
        required_fields.append('employee_id')

        # Handle array payload
    if isinstance(request_data, list):
        if not request_data:
            raise ValueError("Visit data array cannot be empty.")

        visits_data = []
        for i, visit_data in enumerate(request_data):
            try:
                _validate_visit_data(visit_data, required_fields)

                # Add the fixed ID if provided
                if patient_id:
                    visit_data['patient_id'] = patient_id
                if employee_id:
                    visit_data['employee_id'] = employee_id

                visits_data.append(visit_data)
            except ValueError as e:
                raise ValueError(f"Error in visit data at index {i}: {str(e)}")

        return visits_data

        # Handle single object payload
    elif isinstance(request_data, dict):
        _validate_visit_data(request_data, required_fields)

        # Add the fixed ID if provided
        if patient_id:
            request_data['patient_id'] = patient_id
        if employee_id:
            request_data['employee_id'] = employee_id

        return [request_data]

    else:
        raise ValueError("Request data must be either an object or an array of objects.")


@care_visit_api.route('/employee/<employee_id>')
class EmployeeCareVisits(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN, PersonOrganizationRoleEnum.EMPLOYEE])
    def get(self, person: Person, roles: list, organization: Organization, employee_id: str):
        care_visit_service = CareVisitService(config)
        employee_service = EmployeeService(config)

        # If role is employee, check if the employee_id matches the person's employee record
        if PersonOrganizationRoleEnum.EMPLOYEE in roles:
            employee = employee_service.get_employee_by_person_id(person.entity_id, organization.entity_id)
            if employee.entity_id != employee_id:
                return get_failure_response("Access denied: You can only view your own care visits", status_code=403)

                # Get query parameters for date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        care_visits = care_visit_service.get_employee_care_visits_by_date_range(
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id
        )
        return get_success_response(care_visits=care_visits)

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person: Person, roles: list, organization: Organization, employee_id):
        try:
            request_data = request.get_json(force=True)
            visits_data = _process_visit_payload(request_data, employee_id=employee_id)

            care_visit_service = CareVisitService(config)
            

            # Schedule multiple visits
            scheduled_visits = care_visit_service.schedule_multiple_care_visits(
                visits_data=visits_data,
                scheduled_by_id=person.entity_id,
                organization_id=organization.entity_id
            )

            # Convert to dict format for response
            care_visits_data = [visit.as_dict() for visit in scheduled_visits]

            return get_success_response(
                care_visits=care_visits_data,
                count=len(care_visits_data)
            )

        except ValueError as e:
            return get_failure_response(str(e), status_code=400)
        except Exception as e:
            return get_failure_response(f"Error scheduling care visits: {str(e)}", status_code=500)


@care_visit_api.route('/patient/<patient_id>')
class PatientCareVisits(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person: Person, roles: list, organization: Organization, patient_id):
        care_visit_service = CareVisitService(config)
        patient_service = PatientService(config)

        # Get query parameters for date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        care_visits = care_visit_service.get_patient_care_visits_by_date_range(
            start_date=start_date,
            end_date=end_date,
            patient_id=patient_id
        )
        return get_success_response(care_visits=care_visits)

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person: Person, roles: list, organization: Organization, patient_id):
        try:
            request_data = request.get_json(force=True)
            visits_data = _process_visit_payload(request_data, patient_id=patient_id)

            care_visit_service = CareVisitService(config)

            # Schedule multiple visits
            scheduled_visits = care_visit_service.schedule_multiple_care_visits(
                visits_data=visits_data,
                scheduled_by_id=person.entity_id,
                organization_id=organization.entity_id
            )

            # Convert to dict format for response
            care_visits_data = [visit.as_dict() for visit in scheduled_visits]

            return get_success_response(
                care_visits=care_visits_data,
                count=len(care_visits_data)
            )

        except ValueError as e:
            return get_failure_response(str(e), status_code=400)
        except Exception as e:
            return get_failure_response(f"Error scheduling care visits: {str(e)}", status_code=500)


@care_visit_api.route('/<string:care_visit_id>')
class CareVisit(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def delete(self, person, organization, role, care_visit_id):
        care_visit_service = CareVisitService(config)

        # Get the care visit by ID
        care_visit_repo = care_visit_service.care_visit_repo
        care_visit = care_visit_repo.get_one({'entity_id': care_visit_id})

        if not care_visit:
            return get_failure_response("Care visit not found", status_code=404)

            # Set status to cancelled
        care_visit.status = CareVisitStatusEnum.CANCELLED

        # Save the cancelled care visit
        care_visit_repo.delete(care_visit)

        return get_success_response(message="Care visit cancelled successfully")


@care_visit_api.route('/employee/clock_in/<string:care_visit_id>')
class ClockIn(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.EMPLOYEE])
    def post(self, person, organization, role, care_visit_id):
        employee_service = EmployeeService(config)
        care_visit_service = CareVisitService(config)

        required_fields = ['clock_in_time', 'clock_in_latitude', 'clock_in_longitude']
        data = parse_request_body(request, required_fields)
        validate_required_fields(data)

        clock_in_time = datetime.fromisoformat(data['clock_in_time'].replace('Z', ''))
        clock_in_latitude = data.get('clock_in_latitude')
        clock_in_longitude = data.get('clock_in_longitude')

        # Validate longitude and latitude if provided
        if clock_in_longitude is not None and not (-180 <= float(clock_in_longitude) <= 180):
            return get_failure_response(message="Invalid longitude value. Must be between -180 and 180.",
                                        status_code=400)
        if clock_in_latitude is not None and not (-90 <= float(clock_in_latitude) <= 90):
            return get_failure_response(message="Invalid latitude value. Must be between -90 and 90.", status_code=400)

        employee = employee_service.get_employee_by_person_id(person.entity_id, organization.entity_id)
        if not employee:
            return get_failure_response(message="Employee record not found.", status_code=404)

        care_visit = care_visit_service.get_care_visit_by_id(care_visit_id)
        if not care_visit:
            return get_failure_response(message="Care visit not found.", status_code=404)

        if care_visit.employee_id != employee.entity_id:
            return get_failure_response(message="This care visit does not belong to you.", status_code=403)

        if care_visit.organization_id != organization.entity_id:
            return get_failure_response(message="This care visit does not belong to your organization.",
                                        status_code=403)

        scheduled_end_time = care_visit.scheduled_end_time
        if scheduled_end_time and scheduled_end_time < clock_in_time:
            return get_failure_response(
                message="Cannot clock in for a visit that had already ended at the reported clock-in time",
                status_code=400)

        care_visit.status = CareVisitStatusEnum.CLOCKED_IN
        care_visit.clock_in_time = clock_in_time
        care_visit.clock_in_longitude = clock_in_longitude
        care_visit.clock_in_latitude = clock_in_latitude

        updated_visit = care_visit_service.save_care_visit(care_visit)

        return get_success_response(
            message="Successfully clocked in.",
            care_visit=updated_visit.as_dict()
        )


@care_visit_api.route('/employee/clock_out/<string:care_visit_id>')
class ClockOut(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.EMPLOYEE])
    def post(self, person, organization, role, care_visit_id):
        employee_service = EmployeeService(config)
        care_visit_service = CareVisitService(config)

        required_fields = ['clock_out_time', 'clock_out_longitude', 'clock_out_latitude']
        data = parse_request_body(request, required_fields)
        validate_required_fields(data)

        clock_out_time = datetime.fromisoformat(data['clock_out_time'].replace('Z', ''))
        clock_out_longitude = data.get('clock_out_longitude')
        clock_out_latitude = data.get('clock_out_latitude')

        # Validate longitude and latitude if provided
        if clock_out_longitude is not None and not (-180 <= float(clock_out_longitude) <= 180):
            return get_failure_response(message="Invalid longitude value. Must be between -180 and 180.",
                                        status_code=400)
        if clock_out_latitude is not None and not (-90 <= float(clock_out_latitude) <= 90):
            return get_failure_response(message="Invalid latitude value. Must be between -90 and 90.", status_code=400)

        employee = employee_service.get_employee_by_person_id(person.entity_id, organization.entity_id)
        if not employee:
            return get_failure_response(message="Employee record not found.", status_code=404)

        care_visit = care_visit_service.get_care_visit_by_id(care_visit_id)
        if not care_visit:
            return get_failure_response(message="Care visit not found.", status_code=404)

        if care_visit.employee_id != employee.entity_id:
            return get_failure_response(message="This care visit does not belong to you.", status_code=403)

        if care_visit.organization_id != organization.entity_id:
            return get_failure_response(message="This care visit does not belong to your organization.",
                                        status_code=403)

        if care_visit.status != CareVisitStatusEnum.CLOCKED_IN:
            return get_failure_response(message="Cannot clock out without clocking in first", status_code=400)

        care_visit.status = CareVisitStatusEnum.COMPLETED
        care_visit.clock_out_time = clock_out_time
        care_visit.clock_out_longitude = clock_out_longitude
        care_visit.clock_out_latitude = clock_out_latitude

        updated_visit = care_visit_service.save_care_visit(care_visit)

        return get_success_response(
            message="Successfully clocked out.",
            care_visit=updated_visit.as_dict()
        )


@care_visit_api.route('/assign-employee')
class AssignEmployeeToCareSlot(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person: Person, organization: Organization):
        """Assign an employee to a patient care slot by creating a care visit"""
        try:
            request_data = request.get_json(force=True)
            
            # Validate required fields
            required_fields = ['patient_id', 'employee_id', 'visit_date', 'scheduled_start_time', 'scheduled_end_time']
            missing_fields = [field for field in required_fields if field not in request_data]
            if missing_fields:
                return get_failure_response(f"Missing required fields: {', '.join(missing_fields)}", status_code=400)
            
            # Create care visit data
            visit_data = {
                'patient_id': request_data['patient_id'],
                'employee_id': request_data['employee_id'],
                'visit_date': request_data['visit_date'],
                'scheduled_start_time': request_data['scheduled_start_time'],
                'scheduled_end_time': request_data['scheduled_end_time'],
                'patient_care_slot_id': request_data.get('patient_care_slot_id', ''),
                'availability_slot_id': request_data.get('availability_slot_id', ''),
                'employee_name': request_data.get('employee_name', ''),
                'scheduled_by_id': person.entity_id,
                'organization_id': organization.entity_id
            }
            
            care_visit_service = CareVisitService(config)
            
            # Create the care visit
            care_visit = care_visit_service.create_care_visit_from_assignment(visit_data)
            
            return get_success_response(
                message="Employee assigned to care slot successfully",
                data=care_visit.as_dict()
            )
            
        except ValueError as e:
            return get_failure_response(str(e), status_code=400)
        except Exception as e:
            return get_failure_response(f"Error assigning employee: {str(e)}", status_code=500)




@care_visit_api.route('/assign-employee-recurring')
class AssignEmployeeToRecurringPattern(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person: Person , organization: Organization):
        """Assign an employee to ALL slots in a recurring pattern using series_id"""
        try:
            request_data = request.get_json(force=True)     
            
            # Validate required fields
            required_fields = ['patient_id', 'employee_id']
            missing_fields = [field for field in required_fields if field not in request_data]
            if missing_fields:
                return get_failure_response(f"Missing required fields: {', '.join(missing_fields)}", status_code=400)
            
            # Create care visit data for recurring assignment
            visit_data = {
                'patient_id': request_data['patient_id'],
                'employee_id': request_data['employee_id'],
                'series_id': request_data.get('series_id'), 
                'employee_name': request_data.get('employee_name', ''),
                'patient_slot_id':request_data.get('patient_slot_id'),
                'scheduled_by_id': person.entity_id,
                'organization_id': organization.entity_id
            }
            care_visit_service = CareVisitService(config)
            
            # Assign employee to all slots in the recurring pattern
            created_visits = care_visit_service.assign_employee_to_recurring_pattern(visit_data)
            
            return get_success_response(
                message=f"Employee assigned to {len(created_visits)} slots in recurring pattern successfully",
                data=[visit.as_dict() for visit in created_visits],
                count=len(created_visits)
            )
            
        except ValueError as e:
            return get_failure_response(str(e), status_code=400)
        except Exception as e:
            return get_failure_response(f"Error assigning employee to recurring pattern: {str(e)}", status_code=500)


@care_visit_api.route('/employee/process_missed_visits')
class ProcessMissedVisits(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.EMPLOYEE])
    def post(self, person: Person, roles: list, organization: Organization, ):
        employee_service = EmployeeService(config)

        required_fields = ['employee_id', 'current_datetime']
        data = parse_request_body(request, required_fields)
        validate_required_fields(data)

        employee_id = data.get('employee_id')

        # If role is employee, check if the employee_id matches the person's employee record
        if PersonOrganizationRoleEnum.EMPLOYEE in roles:
            employee = employee_service.get_employee_by_person_id(person.entity_id, organization.entity_id)
            if employee.entity_id != employee_id:
                return get_failure_response("Access denied: You can only view your own care visits", status_code=403)

                # Parse the current datetime
        current_datetime = datetime.fromisoformat(data['current_datetime'].replace('Z', ''))

        care_visit_service = CareVisitService(config)
        count = care_visit_service.process_missed_visits(employee_id, current_datetime)

        return get_success_response(
            message=f"Successfully processed missed visits.",
            count=count
        )