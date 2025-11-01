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
from . import permission_routes
from . import profile_routes
from . import email_tracking_routes
from . import email_ab_test_routes
from .webhooks import email_webhooks
from . import file_routes
from . import serve_files_routes

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
    "permission_routes",
    "profile_routes",
    "email_tracking_routes",
    "email_ab_test_routes",
    "email_webhooks",
    "file_routes",
    "serve_files_routes",
]

