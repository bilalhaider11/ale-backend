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
    def get(self, person, organization, role, patient_id):
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
    def post(self, person, organization, role, patient_id):
        
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
