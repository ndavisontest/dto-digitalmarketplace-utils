from __future__ import absolute_import
import json
import logging
import sys
import re
from itertools import product
import requests

from flask import request, current_app, render_template_string
from flask.ctx import has_request_context

from dmutils.email import send_email, EmailError

from pythonjsonlogger.jsonlogger import JsonFormatter as BaseJSONFormatter

LOG_FORMAT = '%(asctime)s %(app_name)s %(name)s %(levelname)s ' \
             '%(request_id)s "%(message)s" [in %(pathname)s:%(lineno)d]'
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

logger = logging.getLogger(__name__)


def init_app(app):
    app.config.setdefault('DM_LOG_LEVEL', 'INFO')
    app.config.setdefault('DM_APP_NAME', 'none')
    app.config.setdefault('DM_LOG_PATH', None)

    @app.after_request
    def after_request(response):
        log_handler = current_app.extensions.get('request_log_handler', None)
        if log_handler:
            log_handler(response)
        else:
            current_app.logger.info('{method} {url} {status}',
                                    extra={
                                        'method': request.method,
                                        'url': request.url,
                                        'status': response.status_code
                                    })
        return response

    logging.getLogger().addHandler(logging.NullHandler())

    del app.logger.handlers[:]

    handlers = get_handlers(app)
    loglevel = logging.getLevelName(app.config['DM_LOG_LEVEL'])
    loggers = [app.logger, logging.getLogger('dmutils'), logging.getLogger('dmapiclient')]
    for logger, handler in product(loggers, handlers):
        logger.addHandler(handler)
        logger.setLevel(loglevel)

    app.logger.info("Logging configured")


def configure_handler(handler, app, formatter):
    handler.setLevel(logging.getLevelName(app.config['DM_LOG_LEVEL']))
    handler.setFormatter(formatter)
    handler.addFilter(AppNameFilter(app.config['DM_APP_NAME']))
    handler.addFilter(RequestIdFilter())

    return handler


def get_handlers(app):
    handlers = []
    standard_formatter = CustomLogFormatter(LOG_FORMAT, TIME_FORMAT)
    json_formatter = JSONFormatter(LOG_FORMAT, TIME_FORMAT)

    # Log to files if the path is set, otherwise log to stderr
    if app.config['DM_LOG_PATH']:
        handler = logging.FileHandler(app.config['DM_LOG_PATH'])
        handlers.append(configure_handler(handler, app, standard_formatter))

        handler = logging.FileHandler(app.config['DM_LOG_PATH'] + '.json')
        handlers.append(configure_handler(handler, app, json_formatter))
    else:
        handler = logging.StreamHandler(sys.stderr)
        handlers.append(configure_handler(handler, app, standard_formatter))

    return handlers


class AppNameFilter(logging.Filter):
    def __init__(self, app_name):
        self.app_name = app_name

    def filter(self, record):
        record.app_name = self.app_name

        return record


class RequestIdFilter(logging.Filter):
    @property
    def request_id(self):
        if has_request_context() and hasattr(request, 'request_id'):
            return request.request_id
        else:
            return 'no-request-id'

    def filter(self, record):
        record.request_id = self.request_id

        return record


class CustomLogFormatter(logging.Formatter):
    """Accepts a format string for the message and formats it with the extra fields"""

    FORMAT_STRING_FIELDS_PATTERN = re.compile(r'\((.+?)\)', re.IGNORECASE)

    def add_fields(self, record):
        for field in self.FORMAT_STRING_FIELDS_PATTERN.findall(self._fmt):
            record.__dict__[field] = record.__dict__.get(field)
        return record

    def format(self, record):
        record = self.add_fields(record)
        msg = super(CustomLogFormatter, self).format(record)

        try:
            msg = msg.format(**record.__dict__)
        except KeyError as e:
            logger.exception("failed to format log message: {} not found".format(e))
        return msg


class JSONFormatter(BaseJSONFormatter):
    def process_log_record(self, log_record):
        rename_map = {
            "asctime": "time",
            "request_id": "requestId",
            "app_name": "application",
        }
        for key, newkey in rename_map.items():
            log_record[newkey] = log_record.pop(key)
        log_record['logType'] = "application"
        try:
            log_record['message'] = log_record['message'].format(**log_record)
        except KeyError as e:
            logger.exception("failed to format log message: {} not found".format(e))
        return log_record


def slack_escape(text):
    """
    Escapes special characters for Slack API.

    https://api.slack.com/docs/message-formatting#how_to_escape_characters
    """
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def notify_team(subject, body, more_info_url=None):
    """
    Generic routine for making simple notifications to the Marketplace team.

    Notification messages should be very simple so that they're compatible with a variety of backends.
    """
    if 'DM_TEAM_SLACK_WEBHOOK' in current_app.config:
        slack_body = slack_escape(body)
        if more_info_url:
            slack_body += '\n' + more_info_url
        data = {
            'attachments': [{
                'title': subject,
                'text': slack_body,
                'fallback': '{} - {} {}'.format(subject, body, more_info_url),
            }],
            'username': 'Marketplace Notifications',
        }
        response = requests.post(
            current_app.config['DM_TEAM_SLACK_WEBHOOK'],
            json=data
        )
        if response.status_code != 200:
            msg = 'Failed to send notification to Slack channel: {} - {}'.format(response.status_code, response.text)
            current_app.logger.error(msg)

    if 'DM_TEAM_EMAIL' in current_app.config:
        email_body = render_template_string(
            '<p>{{ body }}</p>{% if more_info_url %}<a href="{{ more_info_url }}">More info</a>{% endif %}',
            body=body, more_info_url=more_info_url
        )
        try:
            send_email(
                current_app.config['DM_TEAM_EMAIL'],
                email_body,
                subject,
                current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
                current_app.config['DM_GENERIC_ADMIN_NAME'],
            )
        except EmailError as e:
            current_app.logger.error('Failed to send notification email: {}'.format(e.message))
