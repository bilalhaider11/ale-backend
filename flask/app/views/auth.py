from flask_restx import Namespace, Resource
from flask import request
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from common.app_config import config
from common.services import AuthService, PersonService

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
        parsed_body = parse_request_body(request, ['first_name', 'last_name', 'email_address'])
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)

        auth_service.signup(
            parsed_body['email_address'],
            parsed_body['first_name'],
            parsed_body['last_name']
        )
        return get_success_response(message="User signed up successfully and verification email is sent.")


@auth_api.route('/login')
class Login(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'email': {'type': 'string'},
            'password': {'type': 'string'}
        }}
    )
    def post(self):
        parsed_body = parse_request_body(request, ['email', 'password'])
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)
        access_token, expiry = auth_service.login_user_by_email_password(
            parsed_body['email'], 
            parsed_body['password']
        )

        person_service = PersonService(config)
        person = person_service.get_person_by_email_address(email_address=parsed_body['email'])

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
