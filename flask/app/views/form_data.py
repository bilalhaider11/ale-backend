from common.models.person_organization_role import PersonOrganizationRoleEnum
from flask import request
from flask_restx import Namespace, Resource, fields
from common.app_config import config
from common.services.form_data import FormDataService
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from app.helpers.decorators import login_required, organization_required
from common.app_logger import get_logger

logger = get_logger(__name__)

form_data_api = Namespace('form_data', description='Form data operations')

# Define request/response models for API documentation
form_field_model = form_data_api.model('FormField', {
    'entity_id': fields.String(description='Entity ID of the form field'),
    'version_id': fields.String(description='Version ID of the form field'),
    'person_id': fields.String(required=True, description='Person ID'),
    'form_name': fields.String(required=True, description='Form name'),
    'field_name': fields.String(required=True, description='Field name'),
    'value': fields.String(description='Field value')
})

form_data_request_model = form_data_api.model('FormDataRequest', {
    'person_id': fields.String(required=True, description='Person ID'),
    'form_name': fields.String(required=True, description='Form name'),
    'field_name': fields.String(required=True, description='Field name'),
    'value': fields.String(description='Field value')
})


def _format_form_data_response(form_data):
    """Format form data for API response."""
    return {
        'entity_id': form_data.entity_id,
        'version_id': form_data.version,
        'person_id': form_data.person_id,
        'form_name': form_data.form_name,
        'field_name': form_data.field_name,
        'value': form_data.value
    }


@form_data_api.route('')
class FormDataResource(Resource):
    
    @form_data_api.expect(form_data_request_model)
    @form_data_api.response(200, 'Form field saved successfully', form_field_model)
    @form_data_api.response(400, 'Validation error')
    @form_data_api.response(500, 'Internal server error')
    @login_required()
    @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN])
    def post(self, person, organization):
        """
        Save a form field value.
        
        This endpoint saves a single form field value for a person.
        """
        try:
            # Parse and validate request body
            data = parse_request_body(request, ['person_id', 'form_name', 'field_name', 'value'])
            required_fields = ['person_id', 'form_name', 'field_name']
            validate_required_fields(data)
            
            # Get person_id from request and changed_by_id from authenticated user
            person_id = data['person_id']
            
            # Initialize service
            form_data_service = FormDataService(config)
            
            # Save the form field
            form_data = form_data_service.save_form_field(
                person_id=person_id,
                form_name=data['form_name'],
                field_name=data['field_name'],
                value=data.get('value', ''),
                organization_id=organization.entity_id
            )
            
            # Return the saved form data
            return get_success_response(
                message="Form field saved successfully",
                form_data=_format_form_data_response(form_data)
            )
            
        except ValueError as e:
            return get_failure_response(str(e), status_code=400)
        except Exception as e:
            logger.error(f"Error saving form data: {str(e)}")
            return get_failure_response(f"Failed to save form data: {str(e)}", status_code=500)


@form_data_api.route('/<string:person_id>')
class FormDataByPersonResource(Resource):
    
    @form_data_api.response(200, 'Form data retrieved successfully')
    @form_data_api.response(404, 'Person not found')
    @form_data_api.response(500, 'Internal server error')
    @login_required()
    def get(self, person, person_id):
        """
        Get all form data for a person.
        
        This endpoint returns all form fields for the specified person.
        """
        try:
            # Initialize service
            form_data_service = FormDataService(config)
            
            # Get all form data for the person
            form_data_list = form_data_service.get_form_data_by_person(person_id)
            
            # Convert to response format
            form_data_response = [_format_form_data_response(fd) for fd in form_data_list]
            
            return get_success_response(
                message="Form data retrieved successfully",
                form_data=form_data_response,
                count=len(form_data_response)
            )
            
        except ValueError as e:
            return get_failure_response(str(e), status_code=400)
        except Exception as e:
            logger.error(f"Error retrieving form data for person {person_id}: {str(e)}")
            return get_failure_response("Failed to retrieve form data", status_code=500)


@form_data_api.route('/<string:person_id>/<string:form_name>')
class FormDataByPersonAndFormResource(Resource):
    
    @form_data_api.response(200, 'Form data retrieved successfully')
    @form_data_api.response(404, 'Person or form not found')
    @form_data_api.response(500, 'Internal server error')
    @login_required()
    def get(self, person, person_id, form_name):
        """
        Get form data for a specific person and form.
        
        This endpoint returns all form fields for the specified person and form.
        """
        try:
            # Initialize service
            form_data_service = FormDataService(config)
            
            # Get form data for the person and form
            form_data_list = form_data_service.get_form_data_by_person_and_form(person_id, form_name)
            
            # Convert to response format
            form_data_response = [_format_form_data_response(fd) for fd in form_data_list]
            
            return get_success_response(
                message="Form data retrieved successfully",
                form_data=form_data_response,
                count=len(form_data_response)
            )
            
        except ValueError as e: 
            return get_failure_response(str(e), status_code=400)
        except Exception as e:
            logger.error(f"Error retrieving form data for person {person_id}, form {form_name}: {str(e)}")
            return get_failure_response("Failed to retrieve form data", status_code=500)
