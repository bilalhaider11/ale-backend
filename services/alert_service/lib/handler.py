from common.app_logger import logger
from common.app_config import config
from typing import Dict
from common.models.alert import AlertLevelEnum, AlertStatusEnum
from common.services.alert import AlertService
from common.services.alert_person import AlertPersonService
from common.services.person_organization_role import PersonOrganizationRoleService

class AlertMessageHandler:
    """Handler for processing alert-related messages"""
    
    def __init__(self):
        self.alert_service = AlertService(config)
        self.alert_person_service = AlertPersonService(config)
        self.person_organization_role_service = PersonOrganizationRoleService(config)
    
    def process_message(self, message: Dict):
        """
        Handle incoming messages for alert processing
        
        Args:
            message: The message to process
        """
        logger.info("Processing alert message: %s", message)
        
        action = message.get('action')
        if action == 'create_alert':
            
            self.handle_create_alert(message)
        elif action == 'update_alert':
            self.handle_update_alert(message)
        elif action == 'mark_read':
            
            self.handle_mark_read(message)
        else:
            logger.warning("Unknown action in message: %s", action)
    
    def handle_create_alert(self, message: Dict):
        """
        Handle creating a new alert
        
        Args:
            message: The message containing alert data
        """
        data = message

        status = data.get('status', AlertStatusEnum.OPEN.value)
        level = data.get('level', AlertLevelEnum.INFO.value)
        
        if isinstance(status, int):
            status_enum = status
        else:
            status_enum = AlertStatusEnum.OPEN.value
            
        if isinstance(level, int):
            level_enum = level
        else:
            level_enum = AlertLevelEnum.INFO.value
            
        saved_alert = self.alert_service.create_alert(
            organization_id=data.get('organization_id',None),
            title=data.get('area', ''),
            description=data.get('message', ''),
            status=status_enum,
            alert_type=level_enum,
            assigned_to_id=data.get('assigned_to_id', None),
        )
        logger.info("Created alert: %s", saved_alert.entity_id)

        organization_persons = self.person_organization_role_service.get_roles_by_orgnization_id(data.get('organization_id'))
        if organization_persons:
            for person in organization_persons:
                self.alert_person_service.create_alert_person(
                    saved_alert.entity_id,
                    person.person_id
                )
                logger.info("Created alert_person for person: %s", person.person_id)
    
    def handle_update_alert(self, message: Dict):
        """
        Handle updating an existing alert
        
        Args:
            message: The message containing update data
        """
        data = message#.get('data', {})
        alert_id = data.get('alert_id')
        
        if not alert_id:
            logger.error("No alert_id provided for update")
            return
            
        updates = {}
        if 'status' in data:
            updates['status'] = data['status']
        if 'assigned_to_id' in data:
            updates['assigned_to_id'] = data['assigned_to_id']
        if 'message' in data:
            updates['message'] = data['message']
        if 'level' in data:
            updates['level'] = data['level']
            
        # Update status with special handling for transitions
        if 'status' in updates:
            self.alert_service.update_alert_status(alert_id, updates['status'], updates.get('assigned_to_id'))
            updates.pop('status', None)
            updates.pop('assigned_to_id', None)
            
        # Update any remaining fields
        if updates:
            self.alert_service.update_alert_fields(alert_id, updates)
            
        logger.info("Updated alert: %s", alert_id)
    
    def handle_mark_read(self, message: Dict):
        """
        Handle marking an alert as read
        
        Args:
            message: The message containing read data
        """
        data = message
        alert_id = data.get('alert_id')
        person_id = data.get('person_id')
        
        if not alert_id or not person_id:
            logger.error("Missing alert_id or person_id for mark_read")
            return

        self.alert_person_service.mark_alert_as_read(alert_id, person_id)
        
        logger.info("Marked alert %s as read by person %s", alert_id, person_id)



