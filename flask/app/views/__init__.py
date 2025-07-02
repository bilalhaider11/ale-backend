from app.views.auth import auth_api
from app.views.organization import organization_api
from app.views.person import person_api
from app.views.version import version_api
from app.views.current_employee import current_employee_api
from app.views.current_caregiver import current_caregiver_api
from app.views.exclusion_match import exclusion_match_api
from app.views.current_employees_file import current_employees_file_api

def initialize_views(api):
    api.add_namespace(auth_api)
    api.add_namespace(organization_api)
    api.add_namespace(person_api)
    api.add_namespace(version_api)
    api.add_namespace(current_employee_api)
    api.add_namespace(current_caregiver_api)
    api.add_namespace(exclusion_match_api)
    api.add_namespace(current_employees_file_api)
