import pusher
from common.app_config import config
from common.app_logger import get_logger

logger = get_logger(__name__)


class PusherService:
    def __init__(self):
        self.pusher_client = pusher.Pusher(
            app_id=config.PUSHER_APP_ID,
            key=config.PUSHER_KEY,
            secret=config.PUSHER_SECRET,
            cluster=config.PUSHER_CLUSTER,
            ssl=True
        )

    def trigger_verification_update(self, organization_id: str, match_data: dict):
        """
        Trigger a verification update event for a specific organization
        
        Args:
            organization_id (str): The organization ID
            match_data (dict): The updated match data including verification_result and s3_key
        """
        try:
            channel = f"organization-{organization_id}"
            event = "verification-update"
            
            self.pusher_client.trigger(channel, event, {
                'entity_id': match_data.get('entity_id'),
                'matched_entity_id': match_data.get('matched_entity_id'),
                'verification_result': match_data.get('verification_result'),
                's3_key': match_data.get('s3_key'),
                'updated_at': match_data.get('updated_at')
            })
            
            logger.info(f"Triggered verification update for organization {organization_id}, match {match_data.get('entity_id')}")
            
        except Exception as e:
            logger.error(f"Error triggering Pusher event: {str(e)}")
            logger.exception(e)

    def trigger_verification_batch_update(self, organization_id: str, matches_data: list):
        """
        Trigger verification updates for multiple matches at once
        
        Args:
            organization_id (str): The organization ID
            matches_data (list): List of updated match data
        """
        try:
            channel = f"organization-{organization_id}"
            event = "verification-batch-update"
            
            self.pusher_client.trigger(channel, event, {
                'matches': matches_data,
                'updated_at': matches_data[0].get('updated_at') if matches_data else None
            })
            
            logger.info(f"Triggered batch verification update for organization {organization_id}, {len(matches_data)} matches")
            
        except Exception as e:
            logger.error(f"Error triggering Pusher batch event: {str(e)}")
            logger.exception(e) 