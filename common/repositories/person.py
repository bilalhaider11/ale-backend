import uuid
from common.repositories.base import BaseRepository
from common.models.person import Person
from common.app_logger import get_logger

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
