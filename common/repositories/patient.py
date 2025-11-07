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


    def upsert_patient(self, record: Patient, organization_id: str) -> list[Patient]:
        """
        Upsert a list of patient records based on medical_record_number
        and organization_id attributes.

        Args:
            records: List of Patient instances to upsert
            organization_id: The organization ID to filter existing records

        Returns:
            List of upserted Patient records
        """
        
        if not record:
            return []

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
