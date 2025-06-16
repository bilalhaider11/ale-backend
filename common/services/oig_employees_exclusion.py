from typing import List, Dict

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.oig_employees_exclusion import OigEmployeesExclusion
from common.helpers.csv_utils import clean_string, parse_date

logger = get_logger(__name__)


class OigEmployeesExclusionService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.oig_exclusions_repo = self.repository_factory.get_repository(RepoType.OIG_EMPLOYEES_EXCLUSION, message_queue_name="")
    
    def delete_all_exclusions(self) -> bool:
        """Delete all existing OIG exclusion records"""
        logger.info("Deleting all existing OIG exclusion records...")
        return self.oig_exclusions_repo.truncate_table()

    def bulk_import_exclusions(self, rows: List[Dict[str, str]]) -> bool:
        """Import CSV data into oig_employees_exclusion table using batch processing"""
        record_count = len(rows)
        logger.info(f"Inserting {record_count} OIG exclusion records...")
        
        # Process in batches for better performance
        batch_size = 1000
        total_batches = (record_count + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, record_count)
            batch_rows = rows[start_idx:end_idx]
            
            with self.oig_exclusions_repo.adapter:
                for row in batch_rows:
                    record = OigEmployeesExclusion(
                        last_name=clean_string(row.get('LASTNAME')),
                        first_name=clean_string(row.get('FIRSTNAME')),
                        middle_name=clean_string(row.get('MIDNAME')),
                        business_name=clean_string(row.get('BUSNAME')),
                        general=clean_string(row.get('GENERAL')),
                        specialty=clean_string(row.get('SPECIALTY')),
                        upin=clean_string(row.get('UPIN')),
                        npi=clean_string(row.get('NPI')),
                        date_of_birth=parse_date(row.get('DOB')),
                        address=clean_string(row.get('ADDRESS')),
                        city=clean_string(row.get('CITY')),
                        state=clean_string(row.get('STATE')),
                        zip_code=clean_string(row.get('ZIP')),
                        exclusion_type=clean_string(row.get('EXCLTYPE')),
                        exclusion_date=parse_date(row.get('EXCLDATE')),
                        reinstatement_date=parse_date(row.get('REINDATE')),
                        waiver_date=parse_date(row.get('WAIVERDATE')),
                        waiver_state=clean_string(row.get('WVRSTATE'))
                    )
                    
                    self.oig_exclusions_repo.insert_exclusion(record)
            
            logger.info(f"Completed batch {batch_num+1}/{total_batches}")
        
        logger.info("Successfully imported OIG LEIE data")
        return True
