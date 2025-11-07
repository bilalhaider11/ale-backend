from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
import os
import uuid
from common.models.alert import AlertLevelEnum, AlertStatusEnum

from common.helpers.csv_utils import parse_date
from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.patient import Patient
from common.services.s3_client import S3ClientService
from common.services.alert import AlertService
from common.models.alert import AlertLevelEnum, AlertStatusEnum
from common.services.organization import OrganizationService
from common.helpers.csv_utils import get_first_matching_column_value, parse_date_string
from common.services.patients_file import PatientsFileService
from common.models.patients_file import PatientsFile, PatientsFileStatusEnum
from common.services.person import PersonService
from common.tasks.send_message import send_message

logger = get_logger(__name__)

class PatientService:
    
    def __init__(self, config, person_id=None):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.patient_repo = self.repository_factory.get_repository(RepoType.PATIENT, message_queue_name="")
        self.person_repo = self.repository_factory.get_repository(RepoType.PERSON, message_queue_name="")
        self.s3_client = S3ClientService()
        self.bucket_name = config.AWS_S3_BUCKET_NAME
        self.patients_prefix = f"{config.AWS_S3_KEY_PREFIX}patients-list/" 
        self.patient_file_service = PatientsFileService(config)
        self.person_service = PersonService(config)
        self.alert_service = AlertService(config)
        self.organization_service = OrganizationService(config)

    def bulk_import_patients(self, rows: List[Dict[str, str]], organization_id: str, user_id: str) -> int:
        """Import CSV data into patient table using batch processing."""
        record_count = len(rows)
        logger.info(f"Processing {record_count} patient records...")

        # Get all existing patients for this organization
        existing_patients = self.patient_repo.get_many({"organization_id": organization_id})
        
        # Create a map of MRN to patient for quick lookup
        existing_patients_map = {}
        if existing_patients:
            for patient in existing_patients:
                if patient.medical_record_number:
                    existing_patients_map[patient.medical_record_number] = patient

        # Temporary structure to hold patient data with names
        patient_data = []
        count = 0
        for row in rows:
            first_name = get_first_matching_column_value(row, ["first name", "first_name"])
            last_name = get_first_matching_column_value(row, ["last name", "last_name"])
            dob_raw = get_first_matching_column_value(row, ["date of birth", "date_of_birth", "dob"])
            mrn = get_first_matching_column_value(row, ["medical_record_number", "mrn"], match_mode="contains")
            gender = get_first_matching_column_value(row, ["gender"], match_mode="contains")

            if not mrn:
                mrn = self.organization_service.get_next_patient_mrn(organization_id)
                
            if mrn in existing_patients_map:
                logger.warning(
                    f"Duplicate patient MRN detected during bulk import"
                )
    
                # Create an alert
                self.alert_service.create_alert(
                    organization_id=organization_id,
                    title="Duplicate patientMRN Detected",
                    description=(
                        f"Duplicate patient MRN detected during bulk import. "
                        
                    ),
                    alert_type=AlertLevelEnum.WARNING.value,
                    status=AlertStatusEnum.ADDRESSED.value,
                )

            date_of_birth = parse_date(dob_raw)
            
            
            patient = Patient(
                changed_by_id=user_id,
                medical_record_number=mrn,
                organization_id=organization_id
            )
            patient_for_person = patient
            patient_for_person.first_name=first_name
            patient_for_person.last_name=last_name
            patient_for_person.gender=gender
            patient_for_person.date_of_birth=date_of_birth
            
            mrn_to_person_id = self.person_repo.upsert_persons_from_patients(patient_for_person, user_id)
            
            patient.person_id=mrn_to_person_id
            
            self.patient_repo.upsert_patient(patient, organization_id)
            
            count+=1
   
        logger.info(f"Successfully imported {count} patient records")
        return count


    
    def upload_patient_list(self, organization_id: str, person_id: str, file_path: str, original_filename: str = None, file_id=None) -> Dict:
        """
        Upload a patient list file to S3
        
        Args:
            organization_id (str): Organization ID
            person_id (str): ID of the person uploading the file
            file_path (str): Local path to the file
            file_id (str, optional): ID to use for the file, if None a new UUID will be generated
            original_filename (str): Original filename
            
        Returns:
            Dict: Information about the uploaded file
        """
        logger.info(f"Uploading patient list for organization: {organization_id}")
        
        if file_id is None:
            file_id = uuid.uuid4().hex

        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

        # Determine file extension and file type
        file_extension = '.xlsx' if file_path.lower().endswith('.xlsx') else '.csv'
        file_type = 'xlsx' if file_path.lower().endswith('.xlsx') else 'csv'
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_type == 'xlsx' else 'text/csv'
        
        # Define S3 key
        s3_key = f"{self.patients_prefix}{organization_id}/{file_id}"

        # Prepare metadata
        metadata = {
            "upload_date": timestamp,
            "organization_id": organization_id,
            "uploaded_by": person_id
        }
        
        file_size = os.path.getsize(file_path)
        
        if original_filename:
            metadata["original_filename"] = original_filename
        patients_file = PatientsFile(
            entity_id=file_id,
            organization_id=organization_id,
            file_name=original_filename or f"{timestamp}{file_extension}",
            file_size=file_size,
            file_type=file_type,
            s3_key=s3_key,
            uploaded_at=datetime.now(),
            uploaded_by=person_id,
            status=PatientsFileStatusEnum.PENDING,
        )
        

        # Save file metadata to database
        saved_file = self.patient_file_service.save_patient_file(patients_file)
        
        # Upload the file
        self.s3_client.upload_file(
            file_path=file_path,
            s3_key=s3_key,
            metadata=metadata,
            content_type=content_type
        )
        
        
        
        send_message(
            queue_name=self.config.PATIENT_IMPORT_PROCESSOR_QUEUE_NAME,
            data={
                'Records': [{
                    's3': {
                        'bucket': {'name': self.config.AWS_S3_BUCKET_NAME},
                        'object': {
                            'key': s3_key,
                            'metadata': {
                                'organization_id': organization_id,
                                'file_id': file_id,
                                'uploaded_by': person_id
                            }
                        }
                    }
                }]
            }
        )

        # Get file size
        
        
        

        # Create CurrentEmployeesFile instance
        

        result = {
            "file": {
                "url": self.s3_client.generate_presigned_url(s3_key, filename=original_filename or f"{timestamp}{file_extension}"),
            },
            "file_metadata": saved_file
        }
        

        return result  

    def get_all_patients_for_organization(self, organization_id: str) -> List[Patient]:
        """
        Get all patients associated with an organization.
        
        Args:
            organization_id: The organization ID to filter by
            
        Returns:
            List of Patient instances
        """
        return self.patient_repo.get_patients_for_organization(organization_id)
    
    def create_single_patient(self, organization_id: str, user_id: str, first_name: str, last_name: str, date_of_birth: str, mrn: str, gender: str) -> Dict:
 
        dob = parse_date(date_of_birth)
        if not dob:
            raise ValueError(f"Invalid date format: {date_of_birth}")

        if self.patient_repo.get_many(
            {"organization_id": organization_id, "medical_record_number": mrn}
        ):
            raise ValueError(f"Patient with MRN {mrn} already exists in this organization")

        temp = Patient(
            changed_by_id=user_id,
            medical_record_number=mrn,
            organization_id=organization_id,
        )
        temp.first_name = first_name
        temp.last_name = last_name
        temp.date_of_birth = date_of_birth
        temp.gender = gender

        mrn_to_pid = self.person_repo.upsert_persons_from_patients([temp], user_id)
        person_id = mrn_to_pid.get(mrn)

        patient = Patient(
            changed_by_id=user_id,
            medical_record_number=mrn,
            organization_id=organization_id,
            person_id=person_id,
        )
        saved = self.patient_repo.save(patient)

        if person_id:
            person = self.person_repo.get_one({"entity_id": person_id})
            if person:
                saved.first_name = person.first_name
                saved.last_name = person.last_name
                saved.date_of_birth = person.date_of_birth
                saved.gender = person.gender

        logger.info("Successfully created patient with ID: %s", saved.entity_id)
        return saved
        
    def get_patient_by_id(self, entity_id: str, organization_id: str) -> Patient:

        """
        Retrieve an patient record by patient ID.
        
        Args:
            entity_id (str): The unique identifier for the patient.
            organization_id (str): The ID of the organization to filter by.
        
        Returns:
            Patient: The patient record if found, otherwise None.
        """
        return self.patient_repo.get_one({
            'entity_id': entity_id,
            'organization_id': organization_id
        }) 

    def save_patient(self, patient: Patient) -> Patient:
        """
        Save an patient record to the database.
        
        Args:
            patient (Patient): The patient object to save.
        
        Returns:
            Patient: The saved patient object with updated entity_id.
        """
        return self.patient_repo.save(patient)
    
    def make_alert_on_duplicate_patient_MRN(self,organization_entity_id,current_emp_id,alert_service):
        logger.warning(f"Duplicate employee_id detected: {current_emp_id}")

        description = (
            f"Duplicate MRN detected: {current_emp_id} for organization {organization_entity_id}."
        )
        status_ = AlertStatusEnum.ADDRESSED.value
        level = AlertLevelEnum.WARNING.value
        title = "Patient"
        
        alert_service.create_alert(
            organization_id=organization_entity_id,
            title=title,
            description=description,
            alert_type=level,
            status=status_,
            assigned_to_id=current_emp_id
        )