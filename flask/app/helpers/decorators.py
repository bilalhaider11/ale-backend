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
from common.services.organization_partnership import OrganizationPartnershipService
from common.services import OrganizationService, PersonOrganizationRoleService

from common.models import PersonOrganizationRoleEnum



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
    """
    Usage: @organization_required(with_roles=[PersonOrganizationRoleEnum.ADMIN, PersonOrganizationRoleEnum.MANAGER])
    """
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

            person_organization_roles = person_organization_role_service.get_roles_of_person_in_organization(
                person_id=person.entity_id,
                organization_id=organization.entity_id
            )

            if not person_organization_roles:
                return get_failure_response(message="User is not authorized to use this organization.", status_code=401)

            if with_roles is not None:
                allowed_roles = [role.value if hasattr(role, 'value') else str(role) for role in with_roles]
                if not any(role in allowed_roles for role in person_organization_roles):
                    return get_failure_response(
                        message="Unauthorized to perform this action on the organization.", 
                        status_code=403
                    )

            g.roles = person_organization_roles
            g.organization = organization

            # handle arguments based on the function parameters
            func_params = signature(func).parameters
            extra_args = {}
            if 'roles' in func_params:
                extra_args['roles'] = person_organization_roles

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

            person_organization_service = PersonOrganizationRoleService(config)
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


def with_partner_organization_ids():
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            organization = kwargs.get('organization') or getattr(g, 'organization', None)

            if not organization:
                raise Exception("with_partner_organization_ids requires `organization` to be injected by @organization_required")

            organization_partnership_service = OrganizationPartnershipService(config)
            partner_ids = organization_partnership_service.get_active_partner_ids_for_organization(organization.entity_id)

            # handle arguments based on the function parameters
            func_params = signature(func).parameters
            extra_args = {}

            if 'partner_organization_ids' in func_params:
                extra_args['partner_organization_ids'] = partner_ids + [organization.entity_id]

            return func(self, *args, **kwargs, **extra_args)

        return wrapper

    return decorator
