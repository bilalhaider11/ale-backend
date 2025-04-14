import re

from rococo.models import Email as BaseEmail
from rococo.models.versioned_model import ModelValidationError

class Email(BaseEmail):
    
    def validate_email(self):
        errors = []
        # Ensure email_address is a string.
        if not isinstance(self.email, str):
            errors.append("Email address must be a string.")
            raise ModelValidationError(errors)

        # Basic regex for validating an email address.
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(pattern, self.email):
            errors.append("Invalid email address format.")
            
        # Enforce a maximum length based on RFC 5321.
        if len(self.email) > 254:
            errors.append("Email address exceeds maximum length of 254 characters.")
        
        if errors:
            raise ModelValidationError(errors)
