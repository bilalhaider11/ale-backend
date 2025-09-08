from typing import List, Dict

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.physician import Physician
from common.models.person import Person
from common.services.current_employees_file import CurrentEmployeesFileService
from common.services.person import PersonService
from common.helpers.csv_utils import get_first_matching_column_value

logger = get_logger(__name__)


class PhysicianService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.physician_repo = self.repository_factory.get_repository(RepoType.PHYSICIAN, message_queue_name="")
        self.person_repo = self.repository_factory.get_repository(RepoType.PERSON, message_queue_name="")
        self.current_employees_file_service = CurrentEmployeesFileService(config)
        self.person_service = PersonService(config)

    def bulk_import_physicians(self, rows: List[Dict[str, str]], organization_id: str, user_id: str) -> tuple[int, List[Dict[str, str]]]:
        """Import CSV data into physician table using batch processing"""
        record_count = len(rows)
        logger.info(f"Processing {record_count} physician records...")

        # Get all existing physicians for this organization
        existing_physicians = self.physician_repo.get_many({"organization_id": organization_id})

        # Create a map of NPI to physician for quick lookup
        existing_physicians_map = {}
        if existing_physicians:
            for physician in existing_physicians:
                if physician.national_provider_identifier:
                    existing_physicians_map[physician.national_provider_identifier] = physician

        # Temporary structure to hold physician data with names
        physician_data = []
        skipped_entries = []

        for row in rows:
            npi = get_first_matching_column_value(row, ['npi', 'national provider identifier',
                                                        'national_provider_identifier'])
            if not npi:
                logger.info(f"Skipping row without NPI: {row}")
                skipped_entries.append(row)
                continue

            physician_data.append({
                'npi': npi,
                'first_name': get_first_matching_column_value(row, ['first name', 'first_name', 'firstname']),
                'last_name': get_first_matching_column_value(row, ['last name', 'last_name', 'lastname']),
                'date_of_birth': get_first_matching_column_value(row, ['date of birth', 'dob']),
                'existing_physician': existing_physicians_map.get(npi)
            })

        # Create temporary physician objects with name data
        temp_physicians = []
        for data in physician_data:
            physician = Physician(
                changed_by_id=user_id,
                national_provider_identifier=data['npi'],
                date_of_birth=data['date_of_birth'],
                organization_id=organization_id,
                person_id=data['existing_physician'].person_id if data['existing_physician'] else None
            )
            # Temporarily store name data on physician object
            physician.first_name = data['first_name']
            physician.last_name = data['last_name']
            temp_physicians.append(physician)

        # Bulk upsert persons and get NPI to person_id mapping
        npi_to_person_id = self.person_repo.upsert_persons_from_physicians(temp_physicians, user_id)

        # Now create final physician records with person_ids
        records = []
        for data in physician_data:
            record = Physician(
                changed_by_id=user_id,
                national_provider_identifier=data['npi'],
                date_of_birth=data['date_of_birth'],
                organization_id=organization_id,
                person_id=npi_to_person_id.get(data['npi']) or (
                    data['existing_physician'].person_id if data['existing_physician'] else None)
            )
            records.append(record)

        count = len(records)
        self.physician_repo.upsert_physicians(records, organization_id)

        logger.info(
            f"Successfully imported {count} physician records. Skipped {len(skipped_entries)} entries without NPI.")
        return count, skipped_entries
