from typing import List
from common.repositories.base import BaseRepository
from common.models.physician import Physician
from common.app_logger import logger


class PhysicianRepository(BaseRepository):
    MODEL = Physician

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)

    def upsert_physicians(self, records: list[Physician], organization_id: str) -> dict:
        """
        Upsert a list of physician records based on national_provider_identifier
        and organization_id attributes.

        Args:
            records: List of Physician instances to upsert
            organization_id: The organization ID to filter existing records

        Returns:
            dict: Dictionary with 'inserted' and 'updated' counts
        """
        if not records:
            return {'inserted': 0, 'updated': 0}

        existing_physicians = self.get_many({"organization_id": organization_id})

        # Convert existing results to a dictionary keyed by NPI
        existing_physicians_map = {}
        if existing_physicians:
            for physician in existing_physicians:
                key = physician.national_provider_identifier
                existing_physicians_map[key] = physician

        records_to_insert = []
        records_to_update = []

        # Process each record to determine if it should be inserted or updated
        for record in records:
            # Set organization_id if not already set
            if not record.organization_id:
                record.organization_id = organization_id

            key = record.national_provider_identifier

            if key in existing_physicians_map:
                # Record exists, prepare for update
                existing_record = existing_physicians_map[key]
                existing_id = existing_record.entity_id
                existing_person_id = existing_record.person_id

                record.entity_id = existing_id  # Ensure the record has the existing ID for update
                record.version = existing_record.version  # Use the existing version for update
                record.previous_version = existing_record.previous_version
                record.person_id = existing_person_id  # Retain the existing person_id

                records_to_update.append(record)
            else:
                # Record doesn't exist, prepare for insert
                records_to_insert.append(record)

        logger.info("Preparing to insert %s new records and update %s existing records.", len(records_to_insert), len(records_to_update))

        inserted_count = 0
        updated_count = 0

        # Perform batch inserts in chunks
        if records_to_insert:
            for idx, insert_batch in enumerate(self._batch_physicians(records_to_insert, batch_size=100)):
                logger.info("Inserting batch %s of size %s", idx + 1, len(insert_batch))
                inserted_count += self._batch_save_physicians(insert_batch)

        # Perform batch updates in chunks
        if records_to_update:
            for idx, update_batch in enumerate(self._batch_physicians(records_to_update, batch_size=100)):
                logger.info("Updating batch %s of size %s", idx + 1, len(update_batch))
                updated_count += self._batch_save_physicians(update_batch)

        logger.info("Upsert physicians completed: %s records inserted, %s records updated.", inserted_count, updated_count)
        return records_to_insert + records_to_update

    def _batch_physicians(self, records: list[Physician], batch_size: int = 1000):
        """
        Split a list of physician records into batches of specified size.

        Args:
            records: List of Physician instances to batch
            batch_size: Size of each batch (default: 1000)

        Yields:
            List[Physician]: Batches of physician records
        """
        for i in range(0, len(records), batch_size):
            yield records[i:i + batch_size]

    def _batch_save_physicians(self, records: list[Physician]) -> int:
        """
        Save a batch of physician records to the database.
        Args:
            records: List of Physician instances to save
        Returns:
            int: Number of records saved
        """
        if not records:
            return 0
        for record in records:
            record = self.save(record)
        return len(records)
