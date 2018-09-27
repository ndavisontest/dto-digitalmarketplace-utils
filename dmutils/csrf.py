import os
import binascii
from flask import session, request, current_app


TOKEN = '_csrf_token'
OLD_TOKEN = 'csrf_token'
REACT_HEADER_NAME = 'X-CSRFToken'


def random_string(length=32):
    return binascii.b2a_hex(os.urandom(length)).decode('utf-8')


def get_csrf_token():
    if TOKEN not in session:
        session[TOKEN] = random_string()
    return session[TOKEN]


def check_valid_csrf():
    if not current_app.config.get('CSRF_ENABLED') and not current_app.config.get('CSRF_FAKED'):
        return True

    tokens_received = [
        request.form.get(OLD_TOKEN, None),
        request.form.get(TOKEN, None),
        request.headers.get(REACT_HEADER_NAME, None)
    ]
    json = request.get_json()
    if json:
        tokens_received.append(json.get(TOKEN, None))
    tokens_received = set(filter(None, tokens_received))

    tokens_from_session = [
        session.get(TOKEN, None),
        session.get(OLD_TOKEN, None)
    ]
    tokens_from_session = set(filter(None, tokens_from_session))

    intersect = tokens_received.intersection(tokens_from_session)
    return bool(intersect)
