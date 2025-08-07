from common.models.care_visit import CareVisit
from common.repositories.base import BaseRepository


class CareVisitRepository(BaseRepository):
    MODEL = CareVisit

    def get_care_visits(self, start_date = None, end_date = None, employee_id = None, patient_id = None):
        conditions = []
        params = ()

        if start_date:
            conditions.append("cv.visit_date >= %s")
            params += (start_date,)
        if end_date:
            conditions.append("cv.visit_date < %s")
            params += (end_date,)
        if employee_id:
            conditions.append("cv.employee_id = %s")
            params += (employee_id,)
        if patient_id:
            conditions.append("cv.patient_id = %s")
            params += (patient_id,)

        conditions_str = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        query = f"""
            SELECT cv.*, (ps.first_name || ' ' || ps.last_name) AS patient_name FROM care_visit cv
                LEFT JOIN patient p ON cv.patient_id = p.entity_id
                LEFT JOIN person ps ON p.person_id = ps.entity_id
            {conditions_str}
        """

        with self.adapter:
            results = self.adapter.execute_query(query, params)
            output = []
            for result in results:
                patient_name = result.pop('patient_name', None)
                care_visit = self.MODEL(**result)
                care_visit_dict = care_visit.as_dict()
                care_visit_dict['patient_name'] = patient_name
                output.append(care_visit_dict)

            return output
