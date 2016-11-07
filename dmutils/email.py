from __future__ import \
    unicode_literals, \
    absolute_import

import base64
from datetime import datetime, timedelta
import hashlib
import json
import six
from string import Template
import struct
import sys
import textwrap

import boto3
import botocore.exceptions
from flask import current_app
from flask._compat import string_types

import pendulum
from cryptography.fernet import Fernet, InvalidToken


ONE_DAY_IN_SECONDS = 86400


class EmailError(Exception):
    pass


def to_bytes(x):
    if isinstance(x, six.string_types):
        return x.encode('utf-8')
    else:
        return x


def send_email(to_email_addresses, email_body, subject, from_email, from_name, reply_to=None):
    if isinstance(to_email_addresses, string_types):
        to_email_addresses = [to_email_addresses]

    email_body = to_bytes(email_body)
    subject = to_bytes(subject)

    if current_app.config.get('DM_SEND_EMAIL_TO_STDERR', False):
        template = Template(textwrap.dedent("""\
            To: $to
            Subject: $subject
            From: $from_line
            Reply-To: $reply_to

            $body"""))
        sys.stderr.write(template.substitute(
            to=', '.join(to_email_addresses),
            subject=subject,
            from_line='{} <{}>'.format(from_name, from_email),
            reply_to=reply_to,
            body=email_body
        ))
    else:
        try:
            email_client = boto3.client('ses')

            destination_addresses = {
                'ToAddresses': to_email_addresses,
            }
            if 'DM_EMAIL_BCC_ADDRESS' in current_app.config:
                destination_addresses['BccAddresses'] = [current_app.config['DM_EMAIL_BCC_ADDRESS']]

            return_address = current_app.config.get('DM_EMAIL_RETURN_ADDRESS')

            result = email_client.send_email(
                Source=u"{} <{}>".format(from_name, from_email),
                Destination=destination_addresses,
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': email_body,
                            'Charset': 'UTF-8'
                        }
                    }
                },
                ReturnPath=return_address or reply_to or from_email,
                ReplyToAddresses=[reply_to or from_email],
            )
        except botocore.exceptions.ClientError as e:
            current_app.logger.error("An SES error occurred: {error}", extra={'error': e.response['Error']['Message']})
            raise EmailError(e.response['Error']['Message'])

        current_app.logger.info("Sent email: id={id}, email={email_hash}",
                                extra={'id': result['ResponseMetadata']['RequestId'],
                                       'email_hash': hash_email(to_email_addresses[0])})


def generate_token(data, secret_key, salt):
    """
    Matches the itsdangerous functionality, but with encryption (using Fernet).

    The "salt" isn't a cryptographic salt.  Use a different salt for different handlers to avoid replay attacks
    (e.g., a token created for /create-buyer-user being sent by an attacker to /give-user-admin-rights)
    """
    json_data = json.dumps(data)
    fernet = Fernet(to_bytes(secret_key))
    bytestring = b'\0'.join(
        [
            to_bytes(salt),
            to_bytes(json_data)
        ]
    )
    return fernet.encrypt(bytestring)


def decode_token(token, secret_key, salt, max_age_in_seconds=ONE_DAY_IN_SECONDS):
    fernet = Fernet(to_bytes(secret_key))
    cleartext = fernet.decrypt(token, ttl=max_age_in_seconds)
    token_salt, json_data = cleartext.split(b'\0', 1)
    if token_salt != to_bytes(salt):
        raise InvalidToken('bad token')
    return json.loads(json_data.decode('utf-8'))


def hash_email(email):
    m = hashlib.sha256()
    m.update(to_bytes(email))
    return base64.urlsafe_b64encode(m.digest())


def parse_fernet_timestamp(ciphertext):
    """
    Returns timestamp embedded in Fernet-encrypted ciphertext, converted to Python datetime object.

    Decryption should be attempted before using this function, as that does cryptographically strong tests on the
    validity of the ciphertext.
    """
    try:
        decoded = base64.urlsafe_b64decode(ciphertext)
        # This is a value in Unix Epoch time
        epoch_timestamp = struct.unpack('>Q', decoded[1:9])[0]
        timestamp = datetime(1970, 1, 1) + timedelta(seconds=epoch_timestamp)
        return timestamp
    except struct.error as e:
        raise ValueError(e.message)


def decode_password_reset_token(token, data_api_client):
    try:
        decoded = decode_token(
            token,
            current_app.config["SECRET_KEY"],
            current_app.config["RESET_PASSWORD_SALT"],
            ONE_DAY_IN_SECONDS
        )
        timestamp = parse_fernet_timestamp(token)
    except InvalidToken:
        current_app.logger.info('Invalid password reset token {}'.format(token))
        return {'error': 'token_invalid'}

    user = data_api_client.get_user(decoded["user"])
    user_last_changed_password_at = pendulum.parse(
        user['users']['passwordChangedAt']
    )

    if timestamp < user_last_changed_password_at:
        current_app.logger.info("Error changing password: Token generated earlier than password was last changed.")
        return {'error': 'token_invalid'}

    return decoded


def decode_invitation_token(encoded_token, role):
    required_fields = ['email_address', 'supplier_code', 'supplier_name'] if role == 'supplier' else ['email_address']
    try:
        token = decode_token(
            encoded_token,
            current_app.config['SHARED_EMAIL_KEY'],
            current_app.config['INVITE_EMAIL_SALT'],
            7 * ONE_DAY_IN_SECONDS
        )
        if all(field in token for field in required_fields):
            return token
        else:
            raise ValueError('Invitation token is missing required keys')
    except Exception as e:
        try:
            msg = e.message
        except AttributeError:
            msg = str(e)

        current_app.logger.info('Invalid invitation token {}.  Error message: {}'.format(encoded_token, msg))
        return None
