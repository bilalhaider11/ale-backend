import os
import tempfile
from flask import request
from flask_restx import Namespace, Resource

from common.app_config import config
from common.services.current_employee import CurrentEmployeeService
from common.services.current_employees_file import CurrentEmployeesFileService
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.models.current_employees_file import CurrentEmployeesFileStatusEnum

current_employees_file_api = Namespace('current_employees_file', description='Current employees files operations')


@current_employees_file_api.route('/poll')
class CurrentEmployeesFilePoll(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Poll for files in processing. By default, return all files which are not in `done` or `error` status.
        If a list of file_ids is present in the body, then include those files in the response even if they are in `error` status.
        """
        body = request.get_json() or {}
        file_ids = body.get('file_ids') or None

        current_employees_file_service = CurrentEmployeesFileService(config)
        files = current_employees_file_service.poll_files(organization.entity_id, file_ids=file_ids)

        return get_success_response(
            data=files
        )


@current_employees_file_api.route('')
class CurrentEmployeesFileList(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """
        Get all current employees files for the organization.
        """
        current_employees_file_service = CurrentEmployeesFileService(config)
        files = current_employees_file_service.get_files(organization.entity_id, status=CurrentEmployeesFileStatusEnum.DONE)

        return get_success_response(
            data=files
        )


@current_employees_file_api.route('/<string:entity_id>')
class CurrentEmployeesFileDetail(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def delete(self, person, organization, entity_id):
        """
        Delete a current employees file by its entity ID.
        """
        current_employees_file_service = CurrentEmployeesFileService(config)
        current_employees_file_service.delete_file(entity_id, organization.entity_id)

        return get_success_response(
            message="Current employees file deleted successfully"
        )
