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
    PersonOrganizationInvitationService,
    PersonOrganizationRoleService,
    PersonService,
    EmailService,
    EmployeeService,
    PatientService
)

from common.models import Organization
from common.models import PersonOrganizationRoleEnum, Person, CareVisitStatusEnum
from app.helpers.decorators import (login_required,
                                    organization_required,
                                    has_role
                                    )
from common.helpers.exceptions import APIException

# Create the care visits blueprint
care_visit_api = Namespace('care_visit', description="Care Visit-related APIs")

@care_visit_api.route('/employee/<employee_id>')
class EmployeeCareVisits(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN, PersonOrganizationRoleEnum.EMPLOYEE])
    def get(self, person, organization, role, employee_id):
        care_visit_service = CareVisitService(config)
        employee_service = EmployeeService(config)
        
        # If role is employee, check if the employee_id matches the person's employee record
        if role == PersonOrganizationRoleEnum.EMPLOYEE:
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
    def post(self, person, organization, role, employee_id):
        
        # Validate required fields
        required_fields = [
            'patient_id', 'visit_date', 'scheduled_start_time', 
            'scheduled_end_time', 'availability_slot_key', 'patient_care_slot_key'
        ]

        data = parse_request_body(request, required_fields)

        validate_required_fields(data)
        
        # Parse datetime fields
        visit_date = datetime.fromisoformat(data['visit_date'].replace('Z', ''))
        scheduled_start_time = datetime.fromisoformat(data['scheduled_start_time'].replace('Z', ''))
        scheduled_end_time = datetime.fromisoformat(data['scheduled_end_time'].replace('Z', ''))

        care_visit_service = CareVisitService(config)
        
        care_visit = care_visit_service.schedule_care_visit(
            patient_id=data['patient_id'],
            employee_id=employee_id,
            visit_date=visit_date,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            scheduled_by_id=person.entity_id,
            availability_slot_key=data['availability_slot_key'],
            patient_care_slot_key=data['patient_care_slot_key'],
            organization_id=organization.entity_id
        )
        
        return get_success_response(care_visit=care_visit)

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
        
        # Validate required fields
        required_fields = [
            'employee_id', 'visit_date', 'scheduled_start_time', 
            'scheduled_end_time', 'availability_slot_key', 'patient_care_slot_key'
        ]

        data = parse_request_body(request, required_fields)

        validate_required_fields(data)
        
        # Parse datetime fields
        visit_date = datetime.fromisoformat(data['visit_date'].replace('Z', ''))
        scheduled_start_time = datetime.fromisoformat(data['scheduled_start_time'].replace('Z', ''))
        scheduled_end_time = datetime.fromisoformat(data['scheduled_end_time'].replace('Z', ''))

        care_visit_service = CareVisitService(config)
        
        care_visit = care_visit_service.schedule_care_visit(
            patient_id=patient_id,
            employee_id=data['employee_id'],
            visit_date=visit_date,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            scheduled_by_id=person.entity_id,
            availability_slot_key=data['availability_slot_key'],
            patient_care_slot_key=data['patient_care_slot_key'],
            organization_id=organization.entity_id
        )
        
        return get_success_response(care_visit=care_visit)



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
            return get_failure_response(message="Invalid longitude value. Must be between -180 and 180.", status_code=400)
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
            return get_failure_response(message="This care visit does not belong to your organization.", status_code=403)
        
        scheduled_end_time = care_visit.scheduled_end_time
        if scheduled_end_time and scheduled_end_time < clock_in_time:
            return get_failure_response(message="Cannot clock in for a visit that had already ended at the reported clock-in time", status_code=400)
        
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
            return get_failure_response(message="Invalid longitude value. Must be between -180 and 180.", status_code=400)
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
            return get_failure_response(message="This care visit does not belong to your organization.", status_code=403)
        
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

@care_visit_api.route('/employee/process_missed_visits')
class ProcessMissedVisits(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.EMPLOYEE])
    def post(self, person, organization, role):
        employee_service = EmployeeService(config)
        
        required_fields = ['employee_id','current_datetime']
        data = parse_request_body(request, required_fields)
        validate_required_fields(data)
        
        employee_id = data.get('employee_id')

        # If role is employee, check if the employee_id matches the person's employee record
        if role == PersonOrganizationRoleEnum.EMPLOYEE:
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