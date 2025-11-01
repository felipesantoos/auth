"""API routes package"""
from . import auth_routes
from . import client_routes
from . import oauth_routes
from . import mfa_routes
from . import session_routes
from . import email_verification_routes
from . import api_key_routes
from . import passwordless_routes
from . import audit_routes
from . import webauthn_routes
from . import sso_routes

__all__ = [
    "auth_routes",
    "client_routes",
    "oauth_routes",
    "mfa_routes",
    "session_routes",
    "email_verification_routes",
    "api_key_routes",
    "passwordless_routes",
    "audit_routes",
    "webauthn_routes",
    "sso_routes",
]

