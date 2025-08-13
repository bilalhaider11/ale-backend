from flask_restx import Namespace, Resource
from flask import request, g
import requests
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from common.app_config import config
from common.services import AuthService, PersonService, PersonOrganizationInvitationService
from common.services.oauth import OAuthClient
from common.app_logger import logger

# Create the auth blueprint
auth_api = Namespace('auth', description="Auth related APIs")


@auth_api.route('/test')
class Test(Resource):
    def get(self):
        login_data = {
            "username": "test",
            "password": "test"
        }
        return get_success_response(**login_data)


@auth_api.route('/signup')
class Signup(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'first_name': {'type': 'string'},
            'last_name': {'type': 'string'},
            'email_address': {'type': 'string'}
        }}
    )
    def post(self):
        parsed_body = parse_request_body(request, ['first_name', 'last_name', 'email_address', 'invitation_token'])
        invitation_token = parsed_body.pop('invitation_token', None)
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)

        person_id = None
        invitation = None
        if invitation_token:
            invitation_service = PersonOrganizationInvitationService(config)
            invitation = invitation_service.get_invitation_by_token(invitation_token)

            if not invitation:
                return get_failure_response(message="Invalid or expired invitation token.")

            if invitation.email.lower() != parsed_body['email_address'].lower():
                return get_failure_response(message="Invalid email address for the invitation token.")
            
            if invitation.first_name.lower() != parsed_body['first_name'].lower() or \
                invitation.last_name.lower() != parsed_body['last_name'].lower():
                 return get_failure_response(message="Invitation name does not match provided name.")

            person_id = invitation.invitee_id

        person = auth_service.signup_by_email(
            parsed_body['email_address'],
            parsed_body['first_name'],
            parsed_body['last_name'],
            person_id=person_id
        )

        g.person = person

        if invitation_token:
            invitation_service = PersonOrganizationInvitationService(config)
            invitation_service.accept_invitation(invitation, person_id)
            
        return get_success_response(message="User signed up successfully and verification email is sent.")


@auth_api.route('/login', methods=['POST'])
class Login(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'email': {'type': 'string'},
            'password': {'type': 'string'}
        }}
    )
    def post(self):
        parsed_body = parse_request_body(request, ['email', 'password', 'invitation_token'])
        invitation_token = parsed_body.pop('invitation_token', None)
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)
        access_token, expiry = auth_service.login_user_by_email_password(
            parsed_body['email'], 
            parsed_body['password']
        )

        invitation = None
        if invitation_token:
            invitation_service = PersonOrganizationInvitationService(config)
            invitation = invitation_service.get_invitation_by_token(invitation_token)

            if not invitation:
                return get_failure_response(message="Invalid or expired invitation token.", status_code=400)

            if invitation.email.lower() != parsed_body['email'].lower():
                return get_failure_response(message="Invalid email address for the invitation token.")

        person_service = PersonService(config)
        person = person_service.get_person_by_email_address(email_address=parsed_body['email'])
        g.person = person

        if invitation_token:
            invitation_service = PersonOrganizationInvitationService(config)
            invitation_service.accept_invitation(invitation, person.entity_id)

        return get_success_response(person=person.as_dict(), access_token=access_token, expiry=expiry)


@auth_api.route('/forgot_password', doc=dict(description="Send reset password link"))
class ForgotPassword(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'email': {'type': 'string'}
        }}
    )
    def post(self):
        parsed_body = parse_request_body(request, ['email'])
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)
        auth_service.trigger_forgot_password_email(parsed_body.get('email'))

        return get_success_response(message="Password reset email sent successfully.")


@auth_api.route(
    '/reset_password/<string:token>/<string:uidb64>',
    doc=dict(description="Update the password using reset password link")
)
class ResetPassword(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'password': {'type': 'string'}
        }}
    )
    def post(self, token, uidb64):
        parsed_body = parse_request_body(request, ['password'])
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)
        access_token, expiry, person_obj = auth_service.reset_user_password(token, uidb64, parsed_body.get('password'))
        return get_success_response(
            message="Your password has been updated!",
            access_token=access_token,
            expiry=expiry,
            person=person_obj.as_dict()
        )

@auth_api.route('/resend_welcome_email', doc=dict(description="Resend welcome email to user"))
class ResendWelcomeEmail(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'email': {'type': 'string'}
        }}
    )
    def post(self):
        parsed_body = parse_request_body(request, ['email'])
        validate_required_fields(parsed_body)
        auth_service = AuthService(config)
        auth_service.resend_welcome_email(parsed_body.get('email'))

        return get_success_response(message="Welcome email resent successfully.")


@auth_api.route('/<string:provider>/exchange')
class OAuthExchange(Resource):
    def post(self, provider):
        parsed_body = parse_request_body(
            request,
            ['code', 'redirect_uri', 'code_verifier', 'invitation_token']
        )
        invitation_token = parsed_body.pop('invitation_token', None)
        validate_required_fields(parsed_body)

        oauth_client = OAuthClient(config)
        auth_service = AuthService(config)

        # Token exchange + user info retrieval
        if provider == "google":
            token_response = oauth_client.get_google_token(
                parsed_body['code'],
                parsed_body['redirect_uri'],
                parsed_body['code_verifier']
            )
            user_info = oauth_client.get_google_user_info(token_response['access_token'])

        elif provider == "microsoft":
            token_response = oauth_client.get_microsoft_token(
                parsed_body['code'],
                parsed_body['redirect_uri'],
                parsed_body['code_verifier']
            )
            user_info = oauth_client.get_microsoft_user_info(token_response['access_token'])

        else:
            return get_failure_response(message=f"Unsupported provider: {provider}")

        # Normalize name + email
        if provider == "google":
            email = user_info.get('email')
            name = user_info.get('name', '')

        elif provider == "microsoft":
            email = user_info.get('upn') or user_info.get('email')
            name = user_info.get('name', '')

        if not email:
            return get_failure_response(message=f"{provider.capitalize()} user info does not contain email.")

        name_parts = name.split(' ', 1)
        first_name, last_name = name_parts[0], name_parts[1] if len(name_parts) > 1 else ""

        # Invitation logic
        person_id = None
        if invitation_token:
            invitation_service = PersonOrganizationInvitationService(config)
            invitation = invitation_service.get_invitation_by_token(invitation_token)
            if not invitation:
                return get_failure_response(message="Invalid or expired invitation token.")
            if invitation.email.lower() != email.lower():
                return get_failure_response(message="Invalid email address for the invitation token.")
            person_id = invitation.invitee_id
            first_name, last_name = invitation.first_name, invitation.last_name

        # Login
        access_token, expiry, person = auth_service.login_user_by_oauth(
            email, first_name, last_name,
            provider=provider,
            provider_data=user_info,
            person_id=person_id
        )
        g.person = person

        if invitation_token:
            invitation_service.accept_invitation(invitation, person.entity_id)

        return get_success_response(person=person.as_dict(), access_token=access_token, expiry=expiry)
