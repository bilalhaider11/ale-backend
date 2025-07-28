from flask_restx import Namespace, Resource
from flask import request, g
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from common.app_config import config
from common.services import AuthService, PersonService, PersonOrganizationInvitationService

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

        person = auth_service.signup(
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
