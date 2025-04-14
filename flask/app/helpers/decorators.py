from functools import wraps
from flask import request
from flask import g, abort

from app.helpers.response import get_failure_response
from inspect import signature
from common.app_logger import logger
from common.app_config import config

from common.services.email import EmailService
from common.services.person import PersonService
from common.services.auth import AuthService
from common.services.auth import AuthService
from common.services import OrganizationService, PersonOrganizationRoleService



def login_required():
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if 'Authorization' not in request.headers:
                return get_failure_response(message="Authorization header not present", status_code=401)
            
            auth_service = AuthService(config)
            email_service = EmailService(config)
            person_service = PersonService(config)

            data = request.headers['Authorization']
            token = str.replace(str(data), 'Bearer ', '')
            try:
                parsed_token = auth_service.parse_access_token(token)

                if not parsed_token:
                    return get_failure_response(message='Access token is invalid', status_code=401)

                person_id = parsed_token.get('person_id')
                email_id = parsed_token.get('email_id')

                email = email_service.get_email_by_id(email_id)
                person = person_service.get_person_by_id(person_id)

                g.person = person
                g.email = email

            except Exception as e:
                logger.exception(e)
                abort(500)

            # handle arguments based on the function parameters
            func_params = signature(func).parameters
            extra_args = {}

            if 'person' in func_params:
                extra_args['person'] = person

            if 'email' in func_params:
                extra_args['email'] = email

            return func(self, *args, **kwargs, **extra_args)

        return wrapper

    return decorator


def organization_required(with_roles=None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if 'x-organization-id' not in request.headers:
                return get_failure_response(message="x-organization-id header is not present", status_code=401)
            
            person = getattr(g, 'person', None)

            if not person:
                raise Exception("organization_required decorator should be used after login_required decorator.")

            organization_service = OrganizationService(config)
            person_organization_role_service = PersonOrganizationRoleService(config)

            organization_id = request.headers['x-organization-id']
            organization = organization_service.get_organization_by_id(organization_id)
            if not organization:
                return get_failure_response(message='Organization ID is invalid', status_code=403)
            
            person_organization_role = person_organization_role_service.get_role_of_person_in_organization(
                person_id=person.entity_id,
                organization_id=organization.entity_id
            )
            if not person_organization_role:
                return get_failure_response(message="User is not authorized to use this organization.", status_code=401)

            # If with_roles is specified, verify the user's role is allowed.
            if with_roles is not None:
                if person_organization_role.role not in with_roles:
                    return get_failure_response(
                        message="User is not authroized to perform this operation on this organization.", 
                        status_code=403
                    )

            g.role = person_organization_role
            g.organization = organization

            # handle arguments based on the function parameters
            func_params = signature(func).parameters
            extra_args = {}
            if 'role' in func_params:
                extra_args['role'] = person_organization_role

            if 'organization' in func_params:
                extra_args['organization'] = organization

            return func(self, *args, **kwargs, **extra_args)

        return wrapper

    return decorator



def has_role(*allowed_roles):
    """
    A generic decorator to check if a user has one of the allowed roles.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            agency_organization_id = kwargs.get("agency_organization_id")

            person_organization_service = PorService(config)
            # Retrieve all roles for the user
            user_roles = person_organization_service.get_all_by_person_id(person_id=g.person_id)
            roles_list = [role.role for role in user_roles]

            # Check if user has any allowed role
            if not any(role in allowed_roles for role in roles_list):
                return get_failure_response("Access denied: insufficient permissions.", status_code=403)

            # Validate admin role permissions
            if PersonOrganizationRoleEnum.ADMIN in roles_list:
                is_super_admin = g.user_organization_name.lower() == config.SUPER_ADMIN_ORGANIZATION_NAME.lower()
                is_valid_agency = agency_organization_id == g.user_organization_id

                if not is_super_admin and not is_valid_agency:
                    return get_failure_response("Access denied: invalid organization.", status_code=403)

            return func(*args, **kwargs)

        return wrapper

    return decorator
