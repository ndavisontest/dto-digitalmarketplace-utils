import os
import rollbar
from flask import current_app, got_request_exception, request
from flask_login import current_user


def report_exception(app, exception):
    rollbar.report_exc_info(request=request)


def _hook(request, data):
    data['framework'] = 'flask'

    if request:
        data['context'] = str(request.url_rule)

    if hasattr(current_app, 'login_manager') and current_user:
        person = {}
        if hasattr(current_user, 'id'):
            person['id'] = current_user.id
        if hasattr(current_user, 'name'):
            person['username'] = current_user.name
        if hasattr(current_user, 'email_address'):
            person['email'] = current_user.email_address

        data['person'] = person


def init_app(app):
    if app.config.get('ROLLBAR_TOKEN') and not app.config.get('DEBUG', True):
        rollbar.init(
            # access token for the demo app: https://rollbar.com/demo
            app.config['ROLLBAR_TOKEN'],
            # environment name
            app.config['DM_ENVIRONMENT'],
            # server root directory, makes tracebacks prettier
            root=os.path.dirname(os.path.realpath(__file__)),
            # flask already sets up logging
            allow_logging_basic_config=False)

        # supplement base data collected by rollbar
        rollbar.BASE_DATA_HOOK = _hook

        # send exceptions from `app` to rollbar, using flask's signal system.
        got_request_exception.connect(report_exception, app)
