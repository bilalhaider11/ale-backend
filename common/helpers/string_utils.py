import base64
from binascii import Error as BinasciiError
from datetime import datetime, date, time
from decimal import Decimal

_PROTECTED_TYPES = (
    type(None), int, float, Decimal, datetime, date, time,
)
RANDOM_STRING_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'


def normal_url_safe_b64_decode(token: str):
    return base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')


def normal_url_safe_b64_encode(token: str):
    return base64.urlsafe_b64encode(token.encode('utf-8')).decode('utf-8')


def is_protected_type(obj):
    """Determine if the object instance is of a protected type.
    Objects of protected types are preserved as-is when passed to
    force_str(strings_only=True).
    """
    return isinstance(obj, _PROTECTED_TYPES)


def urlsafe_base64_encode(s):
    """
    Encode a bytestring to a base64 string for use in URLs. Strip any trailing
    equal signs.
    """
    return base64.urlsafe_b64encode(s).rstrip(b'\n=').decode('ascii')


def urlsafe_base64_decode(s):
    """
    Decode a base64 encoded string. Add back any trailing equal signs that
    might have been stripped.
    """
    s = s.encode()
    try:
        return base64.urlsafe_b64decode(s.ljust(len(s) + len(s) % 4, b'='))
    except (LookupError, BinasciiError) as e:
        raise ValueError(e)


def force_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first for performance reasons.
    if issubclass(type(s), str):
        return s
    if strings_only and is_protected_type(s):
        return s
    if isinstance(s, bytes):
        return str(s, encoding, errors)
    return str(s)


def force_bytes(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first for performance reasons.
    if isinstance(s, bytes):
        if encoding == 'utf-8':
            return s
        else:
            return s.decode('utf-8', errors).encode(encoding, errors)
    if strings_only and is_protected_type(s):
        return s
    if isinstance(s, memoryview):
        return bytes(s)
    return str(s).encode(encoding, errors)
