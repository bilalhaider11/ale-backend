import uuid
from typing import List, Dict
from common.repositories.base import BaseRepository
from common.models.person import Person
from common.app_logger import get_logger
from common.models.patient import Patient

logger = get_logger(__name__)


class PersonRepository(BaseRepository):
    MODEL = Person

    def upsert_person_from_employees(self, employee_records: list, organization_id: str) -> dict:
        """
        Upsert person records for the given employee records.
        
        Args:
            employee_records: List of Employee instances to process
            
        Returns:
            dict: Dictionary with 'inserted', 'updated', and 'unchanged' counts
        """
        logger.info(f"Upserting person records for %s employees...", len(employee_records))
        result = {'inserted': 0, 'updated': 0, 'unchanged': 0}

        person_records = self.get_many({"organization_id": organization_id})
        person_id_map = {record.entity_id: record for record in person_records}

        for employee in employee_records:
            if not employee.first_name and not employee.last_name:
                continue  # Skip if no name information
                
            if employee.person_id:
                # Employee has a person_id, try to update existing person
                existing_person = person_id_map.get(employee.person_id)
                if existing_person:
                    # Update person's name if different
                    if (existing_person.first_name != employee.first_name or 
                        existing_person.last_name != employee.last_name):
                        existing_person.first_name = employee.first_name
                        existing_person.last_name = employee.last_name
                        self.save(existing_person)
                        result['updated'] += 1
                    else:
                        # Person exists and name is unchanged
                        result['unchanged'] += 1
                else:
                    # Person doesn't exist, create new one with the existing person_id
                    new_person = Person(
                        entity_id=employee.person_id,
                        first_name=employee.first_name,
                        last_name=employee.last_name
                    )
                    self.save(new_person)
                    result['inserted'] += 1
            else:
                from common.repositories.factory import RepositoryFactory, RepoType

                # Employee doesn't have a person_id (edge case), create new person
                employee_repo = RepositoryFactory.get_repository(RepoType.EMPLOYEE)
                employee.person_id = uuid.uuid4().hex
                new_person = Person(
                    entity_id=employee.person_id,
                    first_name=employee.first_name,
                    last_name=employee.last_name
                )
                self.save(new_person)
                employee_repo.save(employee)  # Save employee with new person_id
                result['inserted'] += 1

        logger.info(f"Upserting person records for employees completed: %s records inserted, %s records updated, %s records unchanged.", result['inserted'], result['updated'], result['unchanged'])
        return result

    def get_persons_by_ids(self, person_ids: list) -> dict:
        """
        Get multiple persons by their entity IDs.
        
        Args:
            person_ids: List of person entity IDs
            
        Returns:
            dict: Map of entity_id to Person object
        """
        if not person_ids:
            return {}
        
        # Build SQL query with parameterized placeholders
        placeholders = ', '.join(['%s'] * len(person_ids))
        query = f"""
            SELECT * FROM person 
            WHERE entity_id IN ({placeholders})
        """
        
        # Execute query and fetch results
        persons = {}
        try:
            with self.adapter:
                results = self.adapter.execute_query(query, person_ids)
            
            # Convert results to Person objects
            for row in results:
                person = self.MODEL(**row)
                persons[person.entity_id] = person
                        
        except Exception as e:
            logger.error(f"Error fetching persons by IDs: {e}")
            raise
        
        return persons

    def upsert_persons_from_physicians(self, physician_records: list, user_id: str) -> dict:
        """
        Bulk upsert person records for physicians.
        
        Args:
            physician_records: List of Physician instances to process
            organization_id: Organization ID
            user_id: User making the changes
            
        Returns:
            dict: Map of NPI to person_id
        """
        logger.info(f"Upserting person records for %s physicians...", len(physician_records))
        
        # Get all persons with person_ids from physician records
        person_ids = [p.person_id for p in physician_records if p.person_id]
        existing_persons = self.get_persons_by_ids(person_ids)
        
        npi_to_person_id = {}
        persons_to_save = []
        
        for physician in physician_records:
            if not physician.national_provider_identifier:
                continue
                
            # Extract name from physician record (assuming these fields exist)
            first_name = getattr(physician, 'first_name', None)
            last_name = getattr(physician, 'last_name', None)
            
            if physician.person_id and physician.person_id in existing_persons:
                # Update existing person if needed
                person = existing_persons[physician.person_id]
                updated = False
                
                if first_name and person.first_name != first_name:
                    person.first_name = first_name
                    updated = True
                if last_name and person.last_name != last_name:
                    person.last_name = last_name
                    updated = True
                    
                if updated:
                    person.changed_by_id = user_id
                    persons_to_save.append(person)
                    
                npi_to_person_id[physician.national_provider_identifier] = physician.person_id
                
            elif first_name or last_name:
                # Create new person
                new_person = Person(
                    first_name=first_name,
                    last_name=last_name,
                    changed_by_id=user_id
                )
                persons_to_save.append(new_person)
                npi_to_person_id[physician.national_provider_identifier] = new_person.entity_id
        
        # Batch save all persons
        if persons_to_save:
            for person in persons_to_save:
                self.save(person)
        
        logger.info(f"Upserted %s person records", len(persons_to_save))
        return npi_to_person_id

    def upsert_persons_from_patients(self, patients: List, user_id: str) -> Dict[str, str]:
        """
        Bulk upsert persons from patient data and return MRN to person_id mapping.
        
        Args:
            patients: List of Patient objects with temporary first_name, last_name, date_of_birth and gender attributes
            user_id: ID of the user making the changes
            
        Returns:
            Dict mapping MRN to person_id
        """
        mrn_to_person_id = {}
        
        for patient in patients:
            if not (hasattr(patient, 'first_name') or hasattr(patient, 'last_name')):
                continue
                
            # Check if person already exists (if patient has person_id)
            if patient.person_id:
                person = self.get_one({"entity_id": patient.person_id})
                if person:
                    # Update existing person
                    person.first_name = getattr(patient, 'first_name', person.first_name)
                    person.last_name = getattr(patient, 'last_name', person.last_name)
                    person.date_of_birth = getattr(patient, 'date_of_birth', person.date_of_birth)
                    person.gender = getattr(patient, 'gender', person.gender)
                    person.changed_by_id = user_id
                    self.save(person)
                    if patient.medical_record_number:
                        mrn_to_person_id[patient.medical_record_number] = person.entity_id
                    continue
            
            # Create new person
            person = Person(
                first_name=getattr(patient, 'first_name', None),
                last_name=getattr(patient, 'last_name', None),
                date_of_birth=getattr(patient, 'date_of_birth', None),
                gender=getattr(patient, 'gender', None),
                changed_by_id=user_id
            )
            saved_person = self.save(person)
            
            if patient.medical_record_number:
                mrn_to_person_id[patient.medical_record_number] = saved_person.entity_id
        
        return saved_person.entity_id

    def save_multiple(self, persons: list[Person]):
        """
        Save multiple Person records in a single transaction.
        
        Args:
            persons: List of Person instances to save
        """
        for person in persons:
            person = self.save(person)
        return persons
