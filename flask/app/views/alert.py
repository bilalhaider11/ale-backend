from dataclasses import asdict
from flask_restx import Namespace, Resource
from flask import request
from common.helpers.exceptions import InputValidationError, NotFoundError
from common.app_config import config
from common.app_logger import logger
from common.services.organization import OrganizationService
from common.services.employee import EmployeeService
from common.services.person import PersonService
from common.services.alert import AlertService
from common.services.alert_person import AlertPersonService
from app.helpers.response import get_success_response, get_failure_response
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
        
@alert_api.route('/unread-count')
class AlertPersonOperations(Resource):
    @login_required()
    @organization_required(with_roles= [PersonOrganizationRoleEnum.ADMIN])
    def get(self):
        try: 
            person_service = PersonService(config)
            alert_person_service = AlertPersonService(config)
            
            Unread_alerts = alert_person_service.get_unread_alerts_for_person(person_id)
            print("unread alerts: ",Unread_alerts)
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
                
                print(alert_id,person_id)
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
        
        

