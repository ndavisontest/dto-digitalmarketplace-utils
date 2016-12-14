import os
import rollbar
from flask import got_request_exception, request
from flask_login import current_user


def report_exception(app, exception):
    rollbar.report_exc_info(request=request)


def _hook(request, data):
    data['framework'] = 'flask'

    if request:
        data['context'] = str(request.url_rule)

    if current_user:
        data['person'] = {"id": current_user.id, "username": current_user.name, "email": current_user.email_address}


def init_app(app):
    if app.config.get('ROLLBAR_TOKEN'):
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
