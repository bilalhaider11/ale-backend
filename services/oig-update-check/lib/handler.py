import requests
import csv
import io
from datetime import datetime, date
from bs4 import BeautifulSoup
from typing import Optional, List, Dict

from common.app_logger import get_logger
from common.app_config import config
from common.services.oig_employees_exclusion import OigEmployeesExclusionService
from common.services.oig_exclusions_check import OigExclusionsCheckService

logger = get_logger(__name__)


class OigUpdateHandler:
    def __init__(self):
        self.config = config
        self.oig_exclusions_service = OigEmployeesExclusionService(config)
        self.oig_checks_service = OigExclusionsCheckService(config)

    def get_last_update_from_webpage(self) -> Optional[date]:
        """
        Scrape the OIG webpage to get the 'Last Update' date from the specific HTML structure
        """
        try:
            response = requests.get(self.config.OIG_WEBPAGE_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            alert_body = soup.find('div', class_='usa-alert-body')
            if alert_body:
                # Look for h3 with class usa-alert-heading
                heading = alert_body.find('h3', class_='usa-alert-heading')
                if heading:
                    date_text = heading.get_text().strip()
                    try:
                        # Parse date in MM-DD-YYYY format
                        return datetime.strptime(date_text, '%m-%d-%Y').date()
                    except ValueError:
                        logger.warning(f"Could not parse date from heading: {date_text}")
            
            # Fallback to regex patterns if the specific structure isn't found
            text = soup.get_text()
            import re
            patterns = [
                r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY format
                r'Last Update[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
                r'Updated[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
                r'Last Modified[:\s]+(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    try:
                        # Try MM-DD-YYYY format first
                        if '-' in date_str:
                            return datetime.strptime(date_str, '%m-%d-%Y').date()
                        else:
                            return datetime.strptime(date_str, '%m/%d/%Y').date()
                    except ValueError:
                        continue
            
            logger.warning("Could not find 'Last Update' date on OIG webpage")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching last update date from webpage: {str(e)}")
            return None

    def download_csv_data(self) -> Optional[List[Dict[str, str]]]:
        """
        Download the CSV data from OIG website
        """
        try:
            logger.info("Downloading OIG LEIE CSV data...")
            response = requests.get(self.config.OIG_CSV_DOWNLOAD_URL, timeout=300)  # 5 minute timeout
            response.raise_for_status()
            
            # Read CSV data using csv module
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)
            rows = list(reader)
            
            logger.info(f"Successfully downloaded CSV with {len(rows)} records")
            return rows
            
        except Exception as e:
            logger.error(f"Error downloading CSV data: {str(e)}")
            return None

    def process_update_check(self):
        """
        Main method to process the OIG update check
        """
        try:
            # Get last update date from webpage
            webpage_last_update = self.get_last_update_from_webpage()
            
            if webpage_last_update is None:
                self.oig_checks_service.log_check_result('check_failed')
                return
            
            # Get last successful import date
            last_import_date = self.oig_checks_service.get_last_successful_import_date()
            
            # Check if update is needed
            if last_import_date and webpage_last_update <= last_import_date:
                logger.info("No update needed - data is current")
                self.oig_checks_service.log_check_result('no_update', webpage_last_update)
                return
            
            # Download and import new data
            logger.info("Update available - downloading new data...")
            csv_data = self.download_csv_data()
            
            if csv_data is None or not csv_data:
                self.oig_checks_service.log_check_result('import_failed', webpage_last_update)
                return
            
            # Delete existing data and import new data
            delete_success = self.oig_exclusions_service.delete_all_exclusions()
            if not delete_success:
                self.oig_checks_service.log_check_result('import_failed', webpage_last_update)
                return
            
            import_success = self.oig_exclusions_service.bulk_import_exclusions(csv_data)
            
            if import_success:
                self.oig_checks_service.log_check_result('imported', webpage_last_update)
                logger.info("OIG LEIE data successfully updated")
            else:
                self.oig_checks_service.log_check_result('import_failed', webpage_last_update)
                logger.error("Failed to import OIG LEIE data")
                
        except Exception as e:
            logger.error(f"Unexpected error during OIG update check: {str(e)}")
            self.oig_checks_service.log_check_result('check_failed')


def task_handler():
    """
    Main task handler called by the processor
    """
    handler = OigUpdateHandler()
    handler.process_update_check()