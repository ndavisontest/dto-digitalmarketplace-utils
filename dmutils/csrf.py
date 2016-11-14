import os
import binascii
from flask import session, request


TOKEN = '_csrf_token'
REACT_HEADER_NAME = 'X-CSRFToken'


def random_string(length=32):
    return binascii.b2a_hex(os.urandom(length)).decode('utf-8')


def get_csrf_token():
    if TOKEN not in session:
        session[TOKEN] = random_string()
    return session[TOKEN]


def check_valid_header_csrf():
    try:
        return session[TOKEN] == request.headers[REACT_HEADER_NAME]
    except KeyError:
        return False
