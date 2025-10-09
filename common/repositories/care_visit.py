from common.models.care_visit import CareVisit
from common.repositories.base import BaseRepository


class CareVisitRepository(BaseRepository):
    MODEL = CareVisit

    def get_care_visits(self, start_date = None, end_date = None, employee_id = None, patient_id = None):
        conditions = ["cv.active = true"]
        params = ()

        if start_date:
            conditions.append("cv.visit_date >= %s")
            params += (start_date,)
        if end_date:
            conditions.append("cv.visit_date < %s")
            params += (end_date,)
        if employee_id:
            conditions.append("avs.employee_id = %s")
            params += (employee_id,)
        if patient_id:
            conditions.append("pcs.patient_id = %s")
            params += (patient_id,)

        conditions_str = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        query = f"""
            SELECT cv.*,
                pcs.patient_id,
                avs.employee_id,
                (pp.first_name || ' ' || pp.last_name) AS patient_name,
                (pe.first_name || ' ' || pe.last_name) AS employee_name
            FROM care_visit cv
                LEFT JOIN patient_care_slot pcs ON cv.patient_care_slot_id = pcs.entity_id
                LEFT JOIN availability_slot avs ON cv.availability_slot_id = avs.entity_id
                LEFT JOIN patient p ON pcs.patient_id = p.entity_id
                LEFT JOIN employee e ON avs.employee_id = e.entity_id
                LEFT JOIN person pp ON p.person_id = pp.entity_id
                LEFT JOIN person pe ON e.person_id = pe.entity_id
            {conditions_str}
        """

        with self.adapter:
            results = self.adapter.execute_query(query, params)
            output = []
            for result in results:
                patient_id = result.pop('patient_id', None)
                employee_id = result.pop('employee_id', None)
                patient_name = result.pop('patient_name', None)
                employee_name = result.pop('employee_name', None)
                care_visit = self.MODEL(**result)
                care_visit_dict = care_visit.as_dict()
                care_visit_dict['patient_id'] = patient_id
                care_visit_dict['employee_id'] = employee_id
                care_visit_dict['patient_name'] = patient_name
                care_visit_dict['employee_name'] = employee_name
                output.append(care_visit_dict)

            return output
