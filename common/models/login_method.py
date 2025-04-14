from dataclasses import dataclass, field
from typing import Optional
import string

from werkzeug.security import generate_password_hash

from rococo.models.login_method import LoginMethodType
from rococo.models.versioned_model import ModelValidationError
from rococo.models import LoginMethod as BaseLoginMethod


@dataclass
class LoginMethod(BaseLoginMethod):

    raw_password: Optional[str] = field(repr=False, default=None)  # Temporary field

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)
        self.hash_password()

    def hash_password(self):
        if self.raw_password is not None:
            self.validate_raw_password()
            self.password = generate_password_hash(self.raw_password, method='scrypt')
        del self.raw_password

    def validate_raw_password(self):
        allowed_symbols = '!@#$%&()-_[]{};:"./<>?^*`~\',|=+ '
        whitelist = list(string.ascii_uppercase) + list(string.ascii_lowercase) + list(string.digits) + list(allowed_symbols)

        if self.raw_password is None:
            return
        
        unique_v = set(self.raw_password)
        errors = []
        if len(self.raw_password) < 8:
            errors.append("Password must be at least 8 character long")
        if len(self.raw_password) > 100:
            errors.append("Password must be at max 100 character long")
        if not any(map(lambda x: x in unique_v, string.ascii_uppercase)):
            errors.append("Password must contain a uppercase letter")
        if not any(map(lambda x: x in unique_v, string.ascii_lowercase)):
            errors.append("Password must contain a lowercase letter")
        if not any(map(lambda x: x in unique_v, string.digits)):
            errors.append("Password must contain a digit")
        if not any(map(lambda x: x in unique_v, allowed_symbols)):
            errors.append("Password must contain a special character")
        if not all(map(lambda x: x in whitelist, unique_v)):
            errors.append("Password contains an invalid character")

        if errors:
            raise ModelValidationError(errors)

