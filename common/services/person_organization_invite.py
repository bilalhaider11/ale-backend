from common.repositories.factory import RepositoryFactory, RepoType
from common.models import PersonOrganizationInvitation, PersonOrganizationRole, PersonOrganizationRoleEnum
import jwt
import time
from datetime import datetime, timezone
from common.tasks.send_message import MessageSender
from common.helpers.exceptions import APIException

class PersonOrganizationInvitationService:

    VALID_ROLES = PersonOrganizationRoleEnum.valid_values()

    REQUIRED_FIELDS = ["email", "roles"]

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.person_organization_invite_repo = self.repository_factory.get_repository(RepoType.PERSON_ORGANIZATION_INVITATION)
        self.message_sender = MessageSender()
        self.EMAIL_TRANSMITTER_QUEUE_NAME = config.QUEUE_NAME_PREFIX + config.EMAIL_SERVICE_PROCESSOR_QUEUE_NAME

    def create_invitation(self, organization_id, invitee_id, email, roles, invited_by_id, first_name=None, last_name=None):
        """Create a new pending invitation."""
        # Validate roles
        invalid_roles = [role for role in roles if role not in self.VALID_ROLES]
        if invalid_roles:
            raise APIException(f"Invalid roles: {', '.join(invalid_roles)}", 400)

        token = self.generate_invitation_token(organization_id, email, invitee_id, first_name, last_name)

        # Create invitation
        person_organization_invitation = PersonOrganizationInvitation(
            organization_id=organization_id,
            invitee_id=invitee_id,
            email=email,
            roles=",".join(roles),
            token=token,
            status='pending',
            first_name=first_name,
            last_name=last_name,
        )

        return self.person_organization_invite_repo.save(person_organization_invitation)

    def generate_invitation_token(self, organization_id, email, invitee_id, first_name, last_name):
        """Generate a JWT token for the invitation."""
        token = jwt.encode(
            {
                'organization_id': organization_id,
                'email': email,
                'invitee_id': invitee_id,
                'first_name': first_name,
                'last_name': last_name,
                'exp': time.time() + int(self.config.INVITATION_TOKEN_EXPIRE),
            },
            self.config.AUTH_JWT_SECRET,
            algorithm='HS256'
        )
        return token

    def send_invitation_email(self, invitation, organization_name, person):
        """Send an invitation email with an acceptance link."""
        invitation_link = f"{self.config.VUE_APP_URI}/accept-invitation?token={invitation.token}"
        message = {
            "event": "INVITATION",
            "data": {
                "invitation_link": invitation_link,
                "organization_name": organization_name,
                "invitee_name": f"{person.first_name} {person.last_name}",
                "recipient_name": f"{invitation.first_name} {invitation.last_name}",
            },
            "to_emails": [invitation.email],
        }
        self.message_sender.send_message(self.EMAIL_TRANSMITTER_QUEUE_NAME, message)

    def decode_invitation_token(self, token):
        """Validate the token, check authorization, and accept the invitation."""
        try:
            payload = jwt.decode(token, self.config.AUTH_JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise APIException("Invitation has expired.", 400)
        except jwt.InvalidTokenError:
            raise APIException("Invalid invitation token.", 400)

        return  payload

    def get_invitation_by_token(self, token):
        """Retrieve an invitation by its token."""
        return self.person_organization_invite_repo.get_one({"token": token})

    def accept_invitation(self, invitation, invitee_id):
        """Accept an invitation and associate the person with the organization."""

        if invitation.status != 'pending':
            raise APIException("Invalid or expired invitation.", 400)

        roles = invitation.roles.split(",")

        from common.services.person_organization_role import PersonOrganizationRoleService
        person_organization_role_service = PersonOrganizationRoleService(self.config)

        for role in roles:
            por = PersonOrganizationRole(
                person_id=invitee_id,
                organization_id=invitation.organization_id,
                role=role
            )
            person_organization_role_service.save_person_organization_role(por)

        invitation.status = 'accepted'
        invitation.accepted_on = datetime.now(timezone.utc)
        invitation.invitee_id = invitee_id
        self.person_organization_invite_repo.save(invitation)
        return invitation


