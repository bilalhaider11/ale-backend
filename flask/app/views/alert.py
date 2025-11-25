from dataclasses import asdict
from flask_restx import Namespace, Resource
from flask import request
from common.helpers.exceptions import InputValidationError, NotFoundError
from common.app_config import config
from common.app_logger import logger
from common.services.organization import OrganizationService
from common.services.employee import EmployeeService
from common.services.patient import PatientService
from common.services.person import PersonService
from common.services.alert import AlertService
from common.services.alert_person import AlertPersonService
from app.helpers.response import get_success_response, get_failure_response,parse_request_body
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum

alert_api = Namespace('alert', description='Alert operations')
@alert_api.route('')
class AlertList(Resource):
    @login_required()
    @organization_required(with_roles= [PersonOrganizationRoleEnum.ADMIN])
    
    def get(self, organization=None):
        try: 
            organization_id = organization.entity_id if organization else None

            if not organization_id: 
                return get_failure_response("Organization not found.", status_code=404)

            alert_service = AlertService(config)
            alerts = alert_service.get_alerts_by_organization(organization_id)
            
            return get_success_response(
                message="alerts retrieved successfully", 
                data=alerts,
                lenght=len(alerts)
                
            )
        except Exception as e:
            logger.exception("Error fetching alerts for organization_id=%s", organization_id)
            return get_failure_response("error fetching data, raised exception: ",e)
        
@alert_api.route('/unread-count/<string:person_id>')
class AlertPersonOperations(Resource):
    @login_required()
    @organization_required(with_roles= [PersonOrganizationRoleEnum.ADMIN])
    def get(self,person_id:str):
        try: 
            alert_person_service = AlertPersonService(config)
            
            Unread_alerts = alert_person_service.get_unread_alerts_for_person(person_id)
            return get_success_response(  
                message="alerts retrieved successfully", 
                data=Unread_alerts,
                lenght=len(Unread_alerts) 
            )
        except Exception as e:
            logger.exception("Error fetching alerts")
            return get_failure_response("error fetching data, raised exception: ",e)

@alert_api.route('/mark-all-read')  
class AlertPersonOperations(Resource): 
    @login_required()
    @organization_required(with_roles= [PersonOrganizationRoleEnum.ADMIN])
    def put(self):
        alertPersons = request.get_json() or []
        try:
            
            alert_person_service = AlertPersonService(config)
            Seen_alerts = [] 
            for person in alertPersons:
                alert_id = person['alert_id']
                person_id = person['person_id']
                
                seen_alerts = alert_person_service.mark_read( 
                    alert_id=alert_id,
                    person_id=person_id
                )
                Seen_alerts.append(seen_alerts)
                
            return get_success_response(
                message="alerts retrieved successfully", 
                data=Seen_alerts 
            )
        except Exception as e:
            logger.exception("Error fetching alerts")
            return get_failure_response("error fetching data, raised exception: ",e)
        
@alert_api.route('/update-alert')
class UpdateAlertOperations(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def put(self, organization=None):
      
        parsed_body = parse_request_body(request, ['choice'])
        choice = parsed_body.pop('choice', '') or request.json.get('choice', '')
        alert = request.get_json() or {}

        organization_id = organization.entity_id if organization else None
        alert_service = AlertService(config)
        organization_service = OrganizationService(config)

        # Basic validation
        area = alert.get('area') or alert.get('title') or ''
        alert_id = alert.get('alert_id') or alert.get('id') or alert.get('entity_id')
        assigned_to_id = alert.get('assigned_to_id') or alert.get('assignedTo') or alert.get('person_id')

        if not alert_id:
            return get_failure_response("Missing alert_id in request body")

        if area.lower() == 'employee':
            employee_service = EmployeeService(config)
            # Expecting assigned_to_id to be the person_id to find the employee
            
            employee = employee_service.get_employee_by_id(assigned_to_id, organization_id)
            if not employee:
                return get_failure_response("Employee not found for given assigned_to_id/person_id")

            employees = employee_service.get_employees_by_organization_id(organization_id)
            list_of_employee_ids = [emp.employee_id for emp in employees if getattr(emp, 'employee_id', None) is not None]

            if choice == 'auto':
                # generate new unique employee_id
                new_employee_id = employee.employee_id
                # If new_employee_id is None or collides generate until unique
                while (new_employee_id in list_of_employee_ids) or (new_employee_id is None):
                    new_employee_id = organization_service.get_next_employee_id(organization_id)
                    

                employee.employee_id = new_employee_id
                employee_service.save_employee(employee)

                # Update alert with default values if needed
                status = alert.get('status', 0)
                level = alert.get('level', 0)
                message = alert.get('message', '') or 'Auto-assigned employee id'
                result = alert_service.update_alert(status, level, message, assigned_to_id, alert_id)

                return get_success_response(
                    message="alerts and employee updated successfully",
                    data={'employee': employee, 'result': result, 'alert_id': alert_id}
                )

            else:
                # manual
                parsed_manual = parse_request_body(request, [
                    'status',
                    'message',
                    'level',
                    'assigned_to_id',
                    'employee_id',
                ])
                status = parsed_manual.pop('status', alert.get('status', None))
                level = parsed_manual.pop('level', alert.get('level', None))
                message = parsed_manual.pop('message', alert.get('message', None))
                employee_id = parsed_manual.get('employee_id') or alert.get('employee_id')
                assigned_to_id = parsed_manual.get('assigned_to_id') or assigned_to_id

                if not employee_id:
                    return get_failure_response("employee_id is required for manual choice")

                if employee_id in list_of_employee_ids:
                    return get_failure_response(f"This Employee_id already exist. Try another one {employee_id}")

                employee.employee_id = employee_id
                employee_service.save_employee(employee)

                result = alert_service.update_alert(status, level, message, assigned_to_id, alert_id)
                return get_success_response(
                    message="alerts and employee updated successfully",
                    data={'employee': employee, 'result': result, 'alert_id': alert_id}
                )

        else:
            # Patient case
            patient_service = PatientService(config)
            patient_id = alert.get('person_id') or assigned_to_id
            patient = patient_service.get_patient_by_id(patient_id, organization_id)
            if not patient:
                return get_failure_response("Patient not found for given person_id")

            patients = patient_service.get_all_patients_for_organization(organization_id)
            list_of_patient_mrn = [pat.medical_record_number for pat in patients if getattr(pat, 'medical_record_number', None) is not None]

            if choice == 'auto':
                new_patient_mrn = patient.medical_record_number
                while (new_patient_mrn in list_of_patient_mrn) or (new_patient_mrn is None):
                    new_patient_mrn = organization_service.get_next_patient_mrn(organization_id)

                patient.medical_record_number = new_patient_mrn
                patient_service.save_patient(patient)

                status = alert.get('status', 0)
                level = alert.get('level', 0)
                message = alert.get('message', '') or 'Auto-assigned MRN'
                result = alert_service.update_alert(status, level, message, assigned_to_id, alert_id)

                return get_success_response(
                    message="alerts and patient updated successfully",
                    data={'patient': patient, 'result': result, 'alert_id': alert_id}
                )

            else:
                parsed_manual = parse_request_body(request, [
                    'status',
                    'message',
                    'level',
                    'assigned_to_id',
                    'medical_record_number',
                ])
                status = parsed_manual.pop('status', alert.get('status', None))
                level = parsed_manual.pop('level', alert.get('level', None))
                message = parsed_manual.pop('message', alert.get('message', None))
                mrn = parsed_manual.get('medical_record_number') or alert.get('medical_record_number')
                assigned_to_id = parsed_manual.get('assigned_to_id') or assigned_to_id

                if not mrn:
                    return get_failure_response("medical_record_number is required for manual choice")

                if mrn in list_of_patient_mrn:
                    return get_failure_response(f"This medical_record_number already exists. Try another one {mrn}")

                patient.medical_record_number = mrn
                patient_service.save_patient(patient)

                result = alert_service.update_alert(status, level, message, assigned_to_id, alert_id)

                return get_success_response(
                    message="alerts and patient updated successfully",
                    data={'patient': patient, 'result': result, 'alert_id': alert_id}
                )
