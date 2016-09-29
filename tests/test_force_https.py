from tests.helpers import BaseApplicationTest, Config
from dmutils import config, force_https
from flask import Flask


class TestForceHTTPSConfig(Config):
    DM_HTTP_PROTO = "HTTPS"


class TestForceHTTPS(BaseApplicationTest):
    config_object = TestForceHTTPSConfig()

    config = TestForceHTTPSConfig()

    def setup(self):
        super(TestForceHTTPS, self).setup()

        @self.flask.route('/some-page')
        def some_page():
            return 'Interesting content'

    def test_http_view(self):
        res = self.app.get('/some-page')
        assert res.status_code == 301

    def test_https_view(self):
        res = self.app.get('/some-page', base_url="https://localhost")
        assert res.status_code == 200
        assert res.headers.get('Strict-Transport-Security')
