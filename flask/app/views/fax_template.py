from flask import request
from flask_restx import Namespace, Resource
from app.helpers.response import get_success_response, get_failure_response
from app.helpers.decorators import login_required, organization_required
from common.services.fax_template import FaxTemplateService
from common.models.fax_template import FaxTemplate
from common.models.person_organization_role import PersonOrganizationRoleEnum
from common.app_config import config
from common.app_logger import logger

# Create the fax template namespace
fax_template_api = Namespace('fax-templates', description="Fax template APIs")

@fax_template_api.route('')
class FaxTemplateList(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self):
        """
        Get all fax templates for the current organization.
        Query parameters:
        - search: Optional search term to filter templates by name
        """
        try:
            organization_id = request.headers.get('X-Organization-ID')
            if not organization_id:
                return get_failure_response("Organization ID is required", 400)

            service = FaxTemplateService(config)
            
            # Check if search parameter is provided
            search_term = request.args.get('search', '').strip()
            
            if search_term:
                templates = service.search_templates_by_name(organization_id, search_term)
            else:
                templates = service.get_templates_by_organization(organization_id)
            
            # Get template count for metadata
            template_count = service.get_template_count_by_organization(organization_id)
            
            # Convert templates to dict format for JSON response
            template_list = []
            for template in templates:
                template_dict = {
                    'entity_id': template.entity_id,
                    'name': template.name,
                    'body': template.body,
                    'organization_id': template.organization_id,
                    'changed_on': template.changed_on.isoformat() if template.changed_on else None
                }
                template_list.append(template_dict)
            
            return get_success_response(
                templates=template_list,
                metadata={
                    'total_count': template_count,
                    'returned_count': len(template_list),
                    'search_term': search_term if search_term else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error in FaxTemplateList.get: {str(e)}")
            return get_failure_response(f"Error fetching fax templates: {str(e)}", 500)

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self):
        """
        Create a new fax template.
        """
        try:
            organization_id = request.headers.get('X-Organization-ID')
            if not organization_id:
                return get_failure_response("Organization ID is required", 400)

            data = request.get_json()
            if not data:
                return get_failure_response("Request body is required", 400)

            name = data.get('name', '').strip()
            body = data.get('body', '')
            
            if not name:
                return get_failure_response("Template name is required", 400)

            template = FaxTemplate(
                name=name,
                body=body,
                organization_id=organization_id
            )

            service = FaxTemplateService(config)
            created_template = service.create_template(template)
            
            template_dict = {
                'entity_id': created_template.entity_id,
                'name': created_template.name,
                'body': created_template.body,
                'organization_id': created_template.organization_id,
                'changed_on': created_template.changed_on.isoformat() if created_template.changed_on else None
            }
            
            return get_success_response(template=template_dict, message="Fax template created successfully")
            
        except ValueError as e:
            logger.warning(f"Validation error in FaxTemplateList.post: {str(e)}")
            return get_failure_response(f"Validation error: {str(e)}", 400)
        except Exception as e:
            logger.error(f"Error in FaxTemplateList.post: {str(e)}")
            return get_failure_response(f"Error creating fax template: {str(e)}", 500)


@fax_template_api.route('/<string:entity_id>')
class FaxTemplateDetail(Resource):
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def get(self, entity_id):
        """
        Get a specific fax template by ID.
        """
        try:
            organization_id = request.headers.get('X-Organization-ID')
            if not organization_id:
                return get_failure_response("Organization ID is required", 400)

            service = FaxTemplateService(config)
            template = service.get_template_by_id(entity_id, organization_id)
            
            if not template:
                return get_failure_response("Fax template not found", 404)
            
            template_dict = {
                'entity_id': template.entity_id,
                'name': template.name,
                'body': template.body,
                'organization_id': template.organization_id,
                'changed_on': template.changed_on.isoformat() if template.changed_on else None
            }
            
            return get_success_response(template=template_dict)
            
        except Exception as e:
            logger.error(f"Error in FaxTemplateDetail.get: {str(e)}")
            return get_failure_response(f"Error fetching fax template: {str(e)}", 500)

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def put(self, entity_id):
        """
        Update a fax template.
        """
        try:
            organization_id = request.headers.get('X-Organization-ID')
            if not organization_id:
                return get_failure_response("Organization ID is required", 400)

            data = request.get_json()
            if not data:
                return get_failure_response("Request body is required", 400)

            name = data.get('name', '').strip()
            body = data.get('body', '')
            
            if not name:
                return get_failure_response("Template name is required", 400)

            # Update the template
            template = FaxTemplate(
                entity_id=entity_id,
                name=name,
                body=body,
                organization_id=organization_id
            )

            service = FaxTemplateService(config)
            updated_template = service.update_template(template)
            
            template_dict = {
                'entity_id': updated_template.entity_id,
                'name': updated_template.name,
                'body': updated_template.body,
                'organization_id': updated_template.organization_id,
                'changed_on': updated_template.changed_on.isoformat() if updated_template.changed_on else None
            }
            
            return get_success_response(template=template_dict, message="Fax template updated successfully")
            
        except ValueError as e:
            logger.warning(f"Validation error in FaxTemplateDetail.put: {str(e)}")
            return get_failure_response(f"Validation error: {str(e)}", 400)
        except Exception as e:
            logger.error(f"Error in FaxTemplateDetail.put: {str(e)}")
            return get_failure_response(f"Error updating fax template: {str(e)}", 500)

    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def delete(self, entity_id):
        """
        Delete a fax template.
        """
        try:
            organization_id = request.headers.get('X-Organization-ID')
            if not organization_id:
                return get_failure_response("Organization ID is required", 400)

            service = FaxTemplateService(config)
            success = service.delete_template(entity_id, organization_id)
            
            if not success:
                return get_failure_response("Fax template not found", 404)
            
            return get_success_response(message="Fax template deleted successfully")
            
        except Exception as e:
            logger.error(f"Error in FaxTemplateDetail.delete: {str(e)}")
            return get_failure_response(f"Error deleting fax template: {str(e)}", 500)
