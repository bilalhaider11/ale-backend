from flask_restx import Namespace, Resource
from common.models.person_organization_role import PersonOrganizationRoleEnum
from app.helpers.response import get_success_response
from app.helpers.decorators import login_required
from common.app_config import config

person_organization_roles_api = Namespace('person_organization_roles', description="Person Organization roles APIs")

@person_organization_roles_api.route('/roles')
class OrganizationRoles(Resource):
    
    @login_required()
    def get(self, person):
        """
        Get all available organization roles.
        """
        roles = PersonOrganizationRoleEnum.valid_values()
        return get_success_response(roles=roles)
