from typing import List, Optional
import pandas as pd
from datetime import date

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.oig_employees_exclusion import OigEmployeesExclusion

logger = get_logger(__name__)


class OigEmployeesExclusionService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.oig_exclusions_repo = self.repository_factory.get_repository(RepoType.OIG_EMPLOYEES_EXCLUSION, message_queue_name="")
    
    def delete_all_exclusions(self) -> bool:
        """Delete all existing OIG exclusion records"""
        try:
            logger.info("Deleting all existing OIG exclusion records...")
            return self.oig_exclusions_repo.truncate_table()
        except Exception as e:
            logger.error(f"Error deleting OIG exclusions: {str(e)}")
            return False
    
    def bulk_import_exclusions(self, df: pd.DataFrame) -> bool:
        """Import CSV data into oig_employees_exclusion table using batch processing"""
        try:
            record_count = len(df)
            logger.info(f"Inserting {record_count} OIG exclusion records...")
            
            # Process in batches for better performance
            batch_size = 1000
            total_batches = (record_count + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, record_count)
                batch_df = df.iloc[start_idx:end_idx]
                
                with self.oig_exclusions_repo.adapter:
                    for _, row in batch_df.iterrows():
                        record = OigEmployeesExclusion(
                            lastname=self._clean_string(row.get('LASTNAME')),
                            firstname=self._clean_string(row.get('FIRSTNAME')),
                            midname=self._clean_string(row.get('MIDNAME')),
                            busname=self._clean_string(row.get('BUSNAME')),
                            general=self._clean_string(row.get('GENERAL')),
                            specialty=self._clean_string(row.get('SPECIALTY')),
                            upin=self._clean_string(row.get('UPIN')),
                            npi=self._clean_string(row.get('NPI')),
                            dob=self._parse_date(row.get('DOB')),
                            address=self._clean_string(row.get('ADDRESS')),
                            city=self._clean_string(row.get('CITY')),
                            state=self._clean_string(row.get('STATE')),
                            zip=self._clean_string(row.get('ZIP')),
                            excltype=self._clean_string(row.get('EXCLTYPE')),
                            excldate=self._parse_date(row.get('EXCLDATE')),
                            reindate=self._parse_date(row.get('REINDATE')),
                            waiverdate=self._parse_date(row.get('WAIVERDATE')),
                            wvrstate=self._clean_string(row.get('WVRSTATE'))
                        )
                        
                        self.oig_exclusions_repo.insert_exclusion(record)
                
                logger.info(f"Completed batch {batch_num+1}/{total_batches}")
            
            logger.info("Successfully imported OIG LEIE data")
            return True
            
        except Exception as e:
            logger.error(f"Error importing CSV data: {str(e)}")
            return False
    
    def _clean_string(self, value) -> Optional[str]:
        """Clean string values from CSV data"""
        if value is None or pd.isna(value):
            return None
        
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def _parse_date(self, date_str) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str or pd.isna(date_str):
            return None
        
        try:
            from datetime import datetime
            # Try common date formats
            for fmt in ['%Y%m%d', '%m/%d/%Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(str(date_str), fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None
