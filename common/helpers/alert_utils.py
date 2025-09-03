from common.app_config import config
from common.tasks.send_message import send_message
from common.models.alert import AlertLevelEnum, AlertStatusEnum
from typing import Dict, Any, Optional

def send_alert(
    organization_id: str,
    area: str,
    message: str,
    status=AlertStatusEnum.OPEN.value,
    level=AlertLevelEnum.INFO.value
):
    """
    Send a new alert to the alert processor queue.
    
    Args:
        organization_id: The ID of the organization
        area: The area of the alert (e.g., 'Employee Management')
        message: The alert message content
        status: The alert status (default: OPEN)
        level: The alert level (default: INFO)
    """
    alert_message = {
        'action': 'create_alert',
        'data': {
            'organization_id': organization_id,
            'area': area,
            'message': message,
            'status': status,
            'level': level,
        }
    }
    
    send_message(
        queue_name=config.PREFIXED_ALERT_PROCESSOR_QUEUE_NAME,
        data=alert_message
    )

def update_alert(
    alert_id: str,
    updates: Dict[str, Any],
    assigned_to_id: Optional[str] = None
):
    alert_message = {
        'action': 'update_alert',
        'data': {
            'alert_id': alert_id,
            **updates
        }
    }
    
    if assigned_to_id:
        alert_message['data']['assigned_to_id'] = assigned_to_id
    
    send_message(
        queue_name=config.PREFIXED_ALERT_PROCESSOR_QUEUE_NAME,
        data=alert_message
    )

def mark_alert_as_read(alert_id: str, person_id: str):
    alert_message = {
        'action': 'mark_read',
        'data': {
            'alert_id': alert_id,
            'person_id': person_id
        }
    }
    
    send_message(
        queue_name=config.PREFIXED_ALERT_PROCESSOR_QUEUE_NAME,
        data=alert_message
    )
