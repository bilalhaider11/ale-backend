import os
import tempfile
from flask import request
from flask_restx import Namespace, Resource

from common.app_config import config
from common.services.patients_file import PatientsFileService
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.models.patients_file import PatientsFileStatusEnum

patients_file_api = Namespace('patients_file', description='Patients files operations')


@patients_file_api.route('/poll')
class PatientsFilePoll(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Poll for files in processing. By default, return all files which are not in `done` or `error` status.
        If a list of file_ids is present in the body, then include those files in the response even if they are in `error` status.
        """
        body = request.get_json() or {}
        file_ids = body.get('file_ids') or None

        patients_file_service = PatientsFileService(config)
        files = patients_file_service.poll_files(organization.entity_id, file_ids=file_ids)

        return get_success_response(
            data=files
        )


@patients_file_api.route('')
class PatientsFileList(Resource):
    
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, person, organization):
        """
        Get all patients files for the organization.
        """
        patients_file_service = PatientsFileService(config)
        files = patients_file_service.get_files(organization.entity_id, status=PatientsFileStatusEnum.DONE)

        return get_success_response(
            data=files
        )

@patients_file_api.route('/<string:entity_id>')
class PatientsFileDetail(Resource):

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def delete(self, person, organization, entity_id):
        """
        Delete a patients file by its entity ID.
        """
        patients_file_service = PatientsFileService(config)
        patients_file_service.delete_file(entity_id, organization.entity_id)

        return get_success_response(
            message="Patients file deleted successfully"
        )
