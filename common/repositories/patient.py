from common.repositories.base import BaseRepository
from common.models.patient import Patient
from common.app_logger import logger
from datetime import time
from common.models.alert import AlertLevelEnum, AlertStatusEnum



class PatientRepository(BaseRepository):
    MODEL = Patient

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)
        

    def get_patients_for_organization(self, organization_id: str) -> list:
        """
        Get all patients associated with an organization.
        
        Args:
            organization_id: The organization ID to filter by
        
        Returns:
            List of Patient instances
        """
        query = """
            SELECT 
                p.*,
                per.first_name,
                per.last_name,
                per.date_of_birth,
                per.gender
            FROM patient p
            INNER JOIN person per ON p.person_id = per.entity_id
            WHERE p.organization_id = %s AND p.active = true
        """
        
        with self.adapter:
            result = self.adapter.execute_query(query, (organization_id,))
        
        if result:
            patients = []
            for row in result:
                # Extract person fields
                first_name = row.pop('first_name', None)
                last_name = row.pop('last_name', None)
                date_of_birth = row.pop('date_of_birth', None)
                gender = row.pop('gender', None)
                
                # Create Patient instance
                patient = Patient(**row)
                data = patient.as_dict()
                
                data["first_name"] = first_name
                data["last_name"] = last_name
                data["date_of_birth"] = date_of_birth
                data["gender"] = gender
                
                patients.append(data)
            
            return patients
        
        return []


    def upsert_patients(self, record: Patient, organization_id: str) -> list[Patient]:
        """
        Upsert a list of patient records based on medical_record_number
        and organization_id attributes.

        Args:
            records: List of Patient instances to upsert
            organization_id: The organization ID to filter existing records

        Returns:
            List of upserted Patient records
        """
        print("...................................................................................................")
        
        from common.app_config import config
        from common.services import AlertService
        from common.services import OrganizationService
        
        alert_service = AlertService(config)
        
        print("receiving patient record from bulk upload: ",record)
        if not record:
            return []

        existing_patients = self.get_many({"organization_id": organization_id})

        # Convert existing results to a dictionary keyed by MRN
        existing_patients_map = {}
        if existing_patients:
            for patient in existing_patients:
                if patient.medical_record_number:
                    key = patient.medical_record_number
                    existing_patients_map[key] = patient

        records_to_insert = []
        records_to_update = []
        
#######################################################################################################

        # Process each record to determine if it should be inserted or updated
        #here started implementation where previously loop over at this
        
        # Set organization_id if not already set
        if not record.organization_id:
            record.organization_id = organization_id
        key = record.medical_record_number
        
        if key and key in existing_patients_map:
            print(key)
            print(key)
            print(key)
            print(key)
            print(key)
            # Record exists, prepare for update
            existing_record = existing_patients_map[key]
            existing_id = existing_record.entity_id
            existing_person_id = existing_record.person_id
            record.entity_id = existing_id  # Ensure the record has the existing ID for update
            record.version = existing_record.version  # Use the existing version for update
            record.previous_version = existing_record.previous_version
            record.person_id = existing_person_id  # Retain the existing person_id
            
            # Preserve care-related fields if not provided in the import
            if not record.care_period_start:
                record.care_period_start = existing_record.care_period_start
            if not record.care_period_end:
                record.care_period_end = existing_record.care_period_end
            if not record.weekly_quota:
                record.weekly_quota = existing_record.weekly_quota
            if not record.current_week_remaining_quota:
                record.current_week_remaining_quota = existing_record.current_week_remaining_quota
            
            print("----------------------------------------------------------------------------------------------")    
            records_to_insert.append(record)
            
            self._batch_save_patients(record)
            
            alert_service.create_alert( 
                organization_id=organization_id,
                title="Patient Upsert",
                description=f"Patient with MRN {record.medical_record_number} updated. have duplicate record with same MRN. with patient id: {existing_id}",
                alert_type=AlertLevelEnum.WARNING.value,
                status=AlertStatusEnum.ADDRESSED.value,
            )
        else:
            # Record doesn't exist, prepare for insert
            print("8888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888")
            records_to_insert.append(record)
            self._batch_save_patients(record)

        logger.info("Preparing to insert %s new records and update %s existing records.", len(records_to_insert), len(records_to_update))
        
        inserted_count = 0
        updated_count = 0

        logger.info("Upsert patients completed: %s records inserted, %s records updated.", inserted_count, updated_count)
        return records_to_insert + records_to_update


    def _batch_patients(self, records: list[Patient], batch_size: int = 1000):
        """Yield patient records in chunks."""
        for i in range(0, len(records), batch_size):
            yield records[i:i + batch_size]

    def get_all_patient_mrn(self,organization_id=None) -> list:
        
        query = "SELECT medical_record_number FROM patient"
        
        with self.adapter:
            result = self.adapter.execute_query(query if query else None)
            
        if result:
            return result
        
        return result

    def _batch_save_patients(self, record: Patient) -> int:
        """Persist a batch of patients via self.save()."""
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        print("saving patient record: ",record)
        if not record:
            return 0
        self.save(record)
    
    def get_by_patient_mrn(self, medical_record_number: str, organization_id: str) -> Patient:
        """
        Get an employee record by employee_id.

        Args:
            employee_id: The employee ID to search for
            organization_id: The organization ID to filter by
        Returns:
            Employee instance if found, otherwise None
        """
        query = "SELECT * FROM patient WHERE medical_record_number = %s AND organization_id = %s"

        with self.adapter:
            result = self.adapter.execute_query(query, (medical_record_number, organization_id))

        if result:
            return Patient(**result[0])

        return None
