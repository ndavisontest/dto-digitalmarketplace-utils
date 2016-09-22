from flask import session, redirect, request

# A user who hasn't agreed to the most recent version of the terms of use needs to be redirected to a page to review and
# agree to the latest terms.
#
# To minimise disruption, the staleness of the terms agreement is only checked at certain key points in the site, such
# as at login.  Then a flag is set in the session to trigger redirection to the terms review page.


NEEDS_UPDATE_SESSION_VAR = 'terms_update'
REVIEW_URL = '/terms-updated'
TERMS_URL = '/terms-of-use'
WHITELISTED_URLS = (REVIEW_URL, TERMS_URL, '/logout')


def init_app(application):
    static_path = application.static_url_path

    @application.before_request
    def redirect_for_update():
        if needs_acceptance_update() and request.path not in WHITELISTED_URLS \
           and not request.path.startswith(static_path):
            return redirect(REVIEW_URL, code=302)


def set_session_flag(needs_update):
    session[NEEDS_UPDATE_SESSION_VAR] = needs_update


def needs_acceptance_update():
    return session.get(NEEDS_UPDATE_SESSION_VAR, False)
