# -*- coding: utf-8 -*-
# inspired by https://github.com/kennethreitz/flask-sslify
# Copyright (c) 2012, Kenneth Reitz
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from flask import request, redirect


def init_app(app):
    if app.config['DM_HTTP_PROTO'].lower() == "https":
        app.before_request(redirect_to_ssl)
        app.after_request(set_hsts_header)


def redirect_to_ssl():
    """Redirect incoming requests to HTTPS."""
    # Should we redirect?
    if request.url.startswith('http://'):
        # redirect to HTTPS
        url = request.url.replace('http://', 'https://', 1)
        code = 301  # HTTP code 301 Moved Permanently
        r = redirect(url, code=code)
        return r


def set_hsts_header(response):
    """Adds HSTS header to each response."""
    # Should we add STS header?
    if request.url.startswith('https://'):
        response.headers.setdefault('Strict-Transport-Security', 'max-age=86400')  # 1 day in seconds
    return response
