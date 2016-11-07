from flask import render_template_string
import flask_featureflags
from flask_cache import Cache

from dmutils.flask_init import pluralize, init_manager
from dmutils.forms import FakeCsrf
from .helpers import BaseApplicationTest

import pytest


@pytest.mark.parametrize("count,singular,plural,output", [
    (0, "person", "people", "people"),
    (1, "person", "people", "person"),
    (2, "person", "people", "people"),
])
def test_pluralize(count, singular, plural, output):
    assert pluralize(count, singular, plural) == output


class TestDevCacheInit(BaseApplicationTest):

    def setup(self):
        self.cache = Cache()
        self.config.DM_CACHE_TYPE = 'dev'
        super(TestDevCacheInit, self).setup()

    def test_config(self):
        assert self.cache.config['CACHE_TYPE'] == 'simple'


class TestProdCacheInit(BaseApplicationTest):

    def setup(self):
        self.cache = Cache()
        self.config.DM_CACHE_TYPE = 'prod'
        super(TestProdCacheInit, self).setup()

    def test_config(self):
        assert self.cache.config['CACHE_TYPE'] == 'filesystem'


class TestInitManager(BaseApplicationTest):
    def test_init_manager(self):
        init_manager(self.flask, 5000, [])


class TestFeatureFlags(BaseApplicationTest):

    def setup(self):
        self.config.FEATURE_FLAGS = {
            'YES': True,
            'NO': False,
        }
        super(TestFeatureFlags, self).setup()

    def test_flags(self):
        with self.flask.app_context():
            assert flask_featureflags.is_active('YES')
            assert not flask_featureflags.is_active('NO')


class TestCsrf(BaseApplicationTest):

    def setup(self):
        super(TestCsrf, self).setup()

        @self.flask.route('/thing', methods=['POST'])
        def post_endpoint():
            return 'done'

    def test_csrf_okay(self):
        res = self.app.post(
            '/thing',
            data={'csrf_token': FakeCsrf.valid_token},
        )
        assert res.status_code == 200

    def test_csrf_missing(self):
        res = self.app.post('/thing')
        assert res.status_code == 400

    def test_csrf_wrong(self):
        res = self.app.post(
            '/thing',
            data={'csrf_token': 'nope'},
        )
        assert res.status_code == 400


class TestTemplateFilters(BaseApplicationTest):

    # formats themselves are tested in test_formats

    def test_timeformat(self):
        with self.flask.app_context():
            template = '{{ "2000-01-01T00:00:00.000000Z"|timeformat }}'
            result = render_template_string(template)
            assert result.strip()

    def test_shortdateformat(self):
        with self.flask.app_context():
            template = '{{ "2000-01-01T00:00:00.000000Z"|shortdateformat }}'
            result = render_template_string(template)
            assert result.strip()

    def test_dateformat(self):
        with self.flask.app_context():
            template = '{{ "2000-01-01T00:00:00.000000Z"|dateformat }}'
            result = render_template_string(template)
            assert result.strip()

    def test_datetimeformat(self):
        with self.flask.app_context():
            template = '{{ "2000-01-01T00:00:00.000000Z"|datetimeformat }}'
            result = render_template_string(template)
            assert result.strip()
