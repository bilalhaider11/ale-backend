@login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """Update or create a patient record"""
        patient_service = PatientService(config)
        person_service = PersonService(config)
        alert_service = AlertService(config)
        organization_service = OrganizationService(config)
        
        
        parsed_body = parse_request_body(request, [
            'entity_id',
            'first_name',
            'last_name',
            'date_of_birth',
            'medical_record_number',
            'gender',
            'care_period_start',
            'care_period_end',
            'weekly_quota',
        ])

        entity_id = parsed_body.pop('entity_id', None)
        first_name = parsed_body.pop('first_name', None)
        last_name = parsed_body.pop('last_name', None)
        date_of_birth = parsed_body.pop('date_of_birth', None)
        gender = parsed_body.pop('gender', None)
        medical_record_number = parsed_body.pop('medical_record_number', None)
        care_period_start = parsed_body.pop('care_period_start', None)
        care_period_end = parsed_body.pop('care_period_end', None)
        weekly_quota = parsed_body.pop('weekly_quota', None)

        validate_required_fields(parsed_body)
        
        if not medical_record_number:
            MRN_auto_assigner = organization_service.get_next_patient_MRN(organization.entity_id)
            medical_record_number = MRN_auto_assigner
            
        existing_patient = patient_service.patient_repo.get_by_patient_mrn(medical_record_number, organization.entity_id)
        
        print("existing patient: ",existing_patient)
        #logic for duplicate patient
        if existing_patient:
            print("duplicates")
            description = f"Duplicate employee ID detected: Duplicate patient detected: ${medical_record_number} for organization ${organization.entity_id}.${medical_record_number} for organization ${organization.entity_id}."
            status_ =  AlertStatusEnum.ADDRESSED.value
            level = AlertLevelEnum.WARNING.value
            title = 'Patient'
            logger.warning(
                f"Duplicate detected: {medical_record_number} for organization {organization.entity_id}. "
                f"Existing employee: {existing_patient.entity_id} . "
                f"Creating new employee anyway as per requirements."
                
            )
            
            alert_service = AlertService(config)
            try:
                print(alert_service)
                create_duplicateRecord_alert = alert_service.create_alert(
                    organization_id = organization.entity_id,
                    title = title,
                    description = description,
                    alert_type = level,
                    status = status_,
                    assigned_to_id = medical_record_number
                
                )
            except Exception as e:
                logger.error(f"Error processing patient file: {str(e)}")
            
 #####################################################################################       
        if entity_id:
            patient = patient_service.get_patient_by_id(entity_id, organization.entity_id)
            
            
            if not patient:
                return get_failure_response("Patient not found", status_code=404)
            
            patient.medical_record_number = medical_record_number
            patient.care_period_start = care_period_start
            patient.care_period_end = care_period_end
            patient.weekly_quota = weekly_quota

            if patient.person_id:
                person_obj = person_service.get_person_by_id(patient.person_id)
                if person_obj and (
                    person_obj.first_name != first_name 
                    or person_obj.last_name != last_name
                    or person_obj.date_of_birth != date_of_birth
                    or person_obj.gender != gender
                ):
                    person_obj.first_name = first_name
                    person_obj.last_name = last_name
                    person_obj.date_of_birth = date_of_birth
                    person_obj.gender = gender
                    person_service.save_person(person_obj)
            else:
                person_obj = Person(
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=date_of_birth,
                    gender=gender
                )
                person_obj = person_service.save_person(person_obj)
                patient.person_id = person_obj.entity_id

            patient.changed_by_id = person.entity_id
            patient = patient_service.save_patient(patient)
            action = "updated"
        else:
            person_obj = Person(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=gender
            )
            person_obj = person_service.save_person(person_obj)
            
            patient = Patient(
                medical_record_number=medical_record_number,
                care_period_start=care_period_start,
                care_period_end=care_period_end,
                weekly_quota=weekly_quota,
                organization_id=organization.entity_id,
                person_id=person_obj.entity_id,
                changed_by_id=person.entity_id
            )
            
            patient = patient_service.save_patient(patient)
            action = "created"
        
        return get_success_response(
            message=f"Patient {action} successfully",
            data=patient.as_dict()
        )