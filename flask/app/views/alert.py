from dataclasses import asdict
from flask_restx import Namespace, Resource
from common.app_config import config
from common.app_logger import logger
from common.services.alert import AlertService
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum

alert_api = Namespace('alert', description='Alert operations')

@alert_api.route('')
class AlertList(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    
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
        
        

