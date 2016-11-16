from __future__ import absolute_import, unicode_literals

from mock import patch
from .helpers import BaseApplicationTest, Config
from react.render_server import render_server
from hashlib import sha1
import pytest
from react.exceptions import RenderServerError, ReactRenderingError
from react.response import validate_form_data, from_response
from flask import request
from werkzeug.datastructures import MultiDict
import requests
import responses
from six.moves.urllib import parse as urls


class RenderConfig(Config):
    REACT_RENDER = True
    REACT_RENDER_URL = 'http://example.com/render'
    SERVER_NAME = 'http://api'


class TestRenderServer(BaseApplicationTest):
    config = RenderConfig()

    @responses.activate
    @patch('react.render_server.hashlib')
    @patch('react.render_server.get_csrf_token')
    def test_render_server_success(self, get_csrf_token, hashlib):
        get_csrf_token.return_value = 'abc123'

        with self.flask.test_request_context('/test'):
            sha = sha1()
            hashlib.sha1.return_value = sha

            markup = 'hello world!'
            path = '/widget/component.js'
            params = {'hash': sha.hexdigest()}

            responses.add(responses.POST, render_server.url, json={'markup': markup})

            result = render_server.render(path)
            assert result.render() == markup

            assert len(responses.calls) == 1
            req = responses.calls[0].request

            assert req.url == self.config.REACT_RENDER_URL + '?' + urls.urlencode(params)
            assert req.headers['content-type'] == 'application/json'
            assert req.body == '{"path": "' + path + '", ''"serializedProps": "{\\"_serverContext\\": ' \
                '{\\"location\\": \\"/test\\"}, \\"form_options\\": {\\"csrf_token\\": \\"abc123\\"}, ' \
                '\\"options\\": ' \
                '{\\"apiUrl\\": \\"http://api\\", \\"serverRender\\": true}}", ' \
                '"toStaticMarkup": false}'

    @responses.activate
    @patch('react.render_server.get_csrf_token')
    def test_react_render_not_set(self, get_csrf_token):
        get_csrf_token.return_value = 'abc123'

        self.flask.config.update({'REACT_RENDER': None})

        with self.flask.test_request_context('/test'):
            responses.add(responses.POST, render_server.url, json={})

            result = render_server.render('/widget/component.js')
            assert result.render() == ''
            assert result.get_props() == '{"_serverContext": ' \
                                         '{"location": "/test"}, "form_options": {"csrf_token": "abc123"}, ' \
                                         '"options": {"apiUrl": "http://api", ' \
                                         '"serverRender": true}}'

    @responses.activate
    def test_connection_error(self):
        e = requests.exceptions.ConnectionError('mock connection error!')

        with self.flask.test_request_context('/test'):
            responses.add(responses.POST, render_server.url, body=e)

            with pytest.raises(RenderServerError):
                render_server.render('/path')

    @responses.activate
    def test_non_200_status_code(self):
        with self.flask.test_request_context('/test'):
            responses.add(responses.POST, render_server.url, status=400)

            with pytest.raises(RenderServerError):
                render_server.render('/path')

    @responses.activate
    def test_no_markup(self):
        with self.flask.test_request_context('/test'):
            responses.add(responses.POST, render_server.url, json={'markup': None})

            with pytest.raises(ReactRenderingError):
                render_server.render('/path')

    @responses.activate
    def test_render_error(self,):
        with self.flask.test_request_context('/test'):
            responses.add(responses.POST, render_server.url, json={'error': 'an error'})

            with pytest.raises(ReactRenderingError):
                render_server.render('/path')


class TestReactResponse(BaseApplicationTest):
    def test_extract_json_response(self):
        data = MultiDict([('a', '1'), ('b[]', '2'), ('b[]', '3'), ("c.d", '4')])
        data_json = '{"a": "1", "b": ["2","3"], "c": {"d": "4"}}'
        with self.flask.test_request_context('/test', method='POST',
                                             data=data_json, content_type="application/json"):
            response_data = from_response(request)
            assert 'a' in response_data
            assert response_data['a'] == data['a']
            assert 'b' in response_data
            assert 'b[]' not in response_data
            assert response_data['b'] == ['2', '3']
            assert 'c' in response_data
            assert 'd' in response_data['c']
            assert response_data['c']['d'] == '4'

    def test_extract_form_response(self):
        data = MultiDict([('a', '1'), ('b[]', '2'), ('b[]', '3'), ("c.d", '4')])
        with self.flask.test_request_context('/test', method='POST',
                                             data=data):
            response_data = from_response(request)
            assert 'a' in response_data
            assert response_data['a'] == data['a']
            assert 'b' in response_data
            assert 'b[]' not in response_data
            assert response_data['b'] == ['2', '3']
            assert 'c' in response_data
            assert 'd' in response_data['c']
            assert response_data['c']['d'] == '4'

    def test_valid_form(self):
        data = {'key1': 'value1', 'key2': 'value2'}
        required_fields = ['key1', 'key2']
        min_fields = ['key1', ('key2', 5)]
        assert not validate_form_data(data, required_fields)
        assert not validate_form_data(data, min_fields)

    def test_invalid_form(self):
        data = {'key1': 'value1'}
        required_fields = ['key1', 'key2']
        min_fields = [('key1', 10)]
        errors = validate_form_data(data, required_fields)
        min_errors = validate_form_data(data, min_fields)
        assert 'key2' in errors
        assert errors['key2'] == {"required": True}
        assert 'key1' in min_errors
        assert min_errors['key1'] == {"min": True}
