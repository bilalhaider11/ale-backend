import os
import tempfile
import csv
from flask import request
from flask_restx import Namespace, Resource
from openpyxl import load_workbook

from common.app_config import config
from common.app_logger import logger
from common.services.employee import EmployeeService
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.models import Employee
from common.services import (
    PersonOrganizationInvitationService,
    PersonService,
    OrganizationService
)
from common.models import Person

employee_api = Namespace('employee', description='Employee operations')


@employee_api.route('/upload')
class EmployeeListUpload(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Upload a CSV or XLSX file with employee/caregiver or physician data.
        If file contains NPI column, it will be processed as physician data.
        Otherwise, it will be processed as employee data.
        """
        if 'file' not in request.files:
            return get_failure_response("No file provided", status_code=400)
        
        file = request.files['file']
        file_id = request.form.get('file_id', None)
        
        if not file.filename:
            return get_failure_response("No file selected", status_code=400)
        
        # Check if file is a CSV or XLSX
        allowed_extensions = ['.csv', '.xlsx']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return get_failure_response("File must be a CSV or XLSX", status_code=400)
        
        # Save file temporarily with appropriate extension
        file_extension = '.csv' if file.filename.lower().endswith('.csv') else '.xlsx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        try:
            # Detect file category by checking for NPI column
            file_category = "employee"  # default
            
            if file_extension == '.xlsx':
                workbook = load_workbook(temp_file_path, data_only=True)
                worksheet = workbook.active
                
                # Check first 10 rows for header row with NPI
                for row in worksheet.iter_rows(max_row=10, values_only=True):
                    if row and any(cell and 'npi' in str(cell).lower() for cell in row):
                        file_category = "physician"
                        break
            else:
                # CSV file
                with open(temp_file_path, 'r', encoding='utf-8') as csv_file:
                    reader = csv.reader(csv_file)
                    # Check first 10 rows for header row with NPI
                    for i, row in enumerate(reader):
                        if i >= 10:
                            break
                        if row and any(cell and 'npi' in cell.lower() for cell in row):
                            file_category = "physician"
                            break
            
            # Upload file to S3
            employee_service = EmployeeService(config)
            upload_result = employee_service.upload_list_file(
                organization_id=organization.entity_id, 
                person_id=person.entity_id, 
                file_path=temp_file_path,
                file_category=file_category,
                file_id=file_id,
                original_filename=file.filename
            )

            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return get_success_response(
                message=f"File uploaded successfully as {file_category} data",
                upload_info=upload_result,
                file_category=file_category
            )

        except Exception as e:
            # Clean up temporary file in case of error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            logger.exception(e)
            return get_failure_response(
                f"Error uploading file: {str(e)}",
                status_code=500
            )

@employee_api.route('/matches')
class EmployeeListMatches(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """
        Get a list of employees who have matches in the employee_exclusion_match table.
        """
        employee_service = EmployeeService(config)
        matched_employees = employee_service.get_employees_with_matches(organization.entity_id)

        return get_success_response(
            message="Matched employees retrieved successfully",
            data=matched_employees
        )

@employee_api.route('/admin')
class EmployeeAdmin(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):

        employee_service = EmployeeService(config)
        employees = employee_service.get_employees_by_organization(organization.entity_id)
        return get_success_response(
            message="Employees rerieved successfully",
            data=employees
        )

@employee_api.route('')
class EmployeeResource(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.EMPLOYEE])
    def get(self, person, organization):

        employee_service = EmployeeService(config)
        employee = employee_service.get_employee_by_person_id(person.entity_id, organization.entity_id)
        return get_success_response(
            message="Employee rerieved successfully",
            data=employee
        )

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Update or create an employee record.
        """
        employee_service = EmployeeService(config)
        person_service = PersonService(config)
        
        # Parse request body
        parsed_body = parse_request_body(request, [
            'entity_id',
            'first_name',
            'last_name',
            'employee_id',
            'date_of_birth',
            'email_address',
            'social_security_number',
        ])

        entity_id = parsed_body.pop('entity_id', None)
        date_of_birth = parsed_body.pop('date_of_birth', None)
        email_address = parsed_body.pop('email_address', None)
        social_security_number = parsed_body.pop('social_security_number', None)

        validate_required_fields(parsed_body)
        
        if entity_id:
            # Update existing employee
            employee = employee_service.get_employee_by_id(entity_id, organization.entity_id)
            if not employee:
                return get_failure_response("Employee not found", status_code=200)
            
            employee.first_name = parsed_body['first_name']
            employee.last_name = parsed_body['last_name']
            employee.employee_id = parsed_body['employee_id']
            employee.date_of_birth = date_of_birth
            employee.email_address = email_address
            employee.social_security_number = social_security_number

            if employee.person_id:
                person = person_service.get_person_by_id(employee.person_id)
                if person and (person.first_name != employee.first_name or person.last_name != employee.last_name):
                    person.first_name = employee.first_name
                    person.last_name = employee.last_name
                    person_service.save_person(person)

            employee = employee_service.save_employee(employee)
            action = "updated"

        else:
            employee = Employee(
                first_name=parsed_body['first_name'],
                last_name=parsed_body['last_name'],
                employee_id=parsed_body['employee_id'],
                date_of_birth=date_of_birth,
                email_address=email_address,
                social_security_number=social_security_number,
                organization_id=organization.entity_id
            )

            employee = employee_service.save_employee(employee)

            action = "created"
        
        employee_service.trigger_match_for_employee(employee.entity_id)
        return get_success_response(
            message=f"Employee {action} successfully",
            data=employee.as_dict()
        )


@employee_api.route('/invite')
class EmployeeInvite(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Invite an employee to join the organization.
        """
        invitation_service = PersonOrganizationInvitationService(config)
        person_service = PersonService(config)
        employee_service = EmployeeService(config)
        organization_service = OrganizationService(config)

        # Parse request body
        parsed_body = parse_request_body(request, ['employee_id'])
        validate_required_fields({'employee_id': parsed_body['employee_id']})
        employee_id = parsed_body['employee_id']

        # Get the employee record
        employee = employee_service.get_employee_by_id(employee_id, organization.entity_id)
        if not employee:
            return get_failure_response(message="Employee not found.", status_code=404)

        # Get the organization record
        org = organization_service.get_organization_by_id(organization.entity_id)
        if not org:
            return get_failure_response(message="Organization not found.", status_code=404)

        invited_person = None
        
        # Try to find person by person_id if present
        if employee.person_id:
            invited_person = person_service.get_person_by_id(employee.person_id)
        
        # If not found and email is available, try to find by email
        if not invited_person and employee.email_address:
            invited_person = person_service.get_person_by_email_address(employee.email_address)
        
        # If still not found, create a new person
        if not invited_person:
            if not employee.first_name or not employee.last_name:
                return get_failure_response(
                    message="Employee must have first name and last name to create invitation.", 
                    status_code=400
                )
            
            new_person = Person(
                first_name=employee.first_name,
                last_name=employee.last_name
            )
            invited_person = person_service.save_person(new_person)


        # Create and send invitation with employee role
        invitation = invitation_service.create_invitation(
            organization_id=organization.entity_id,
            invitee_id=invited_person.entity_id,
            email=employee.email_address,
            roles=['employee'],
            first_name=employee.first_name,
            last_name=employee.last_name,
            invited_by_id=person.entity_id
        )
        invitation_service.send_invitation_email(invitation, org.name, person)

        employee.person_id = invited_person.entity_id
        employee_service.save_employee(employee)

        return get_success_response(message="Employee invitation sent successfully.")
