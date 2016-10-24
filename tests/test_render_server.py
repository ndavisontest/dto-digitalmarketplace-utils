from mock import patch
from helpers import BaseApplicationTest, Config
from react.render_server import render_server
from requests import Response, ConnectionError
from hashlib import sha1
import pytest
from react.exceptions import RenderServerError, ReactRenderingError


class RenderConfig(Config):
    REACT_RENDER = True
    REACT_RENDER_URL = '/render'
    DM_DATA_API_URL = 'http://api'


class TestRenderServer(BaseApplicationTest):
    config = RenderConfig()

    @patch('react.render_server.hashlib')
    @patch('react.render_server.requests')
    def test_render_server_success(self, requests, hashlib):
        with self.flask.test_request_context('/test'):
            sha = sha1()
            hashlib.sha1.return_value = sha

            res = Response()
            res.status_code = 200
            markup = 'hello world!'
            res.json = lambda: {'markup': markup}
            requests.post.return_value = res

            path = '/widget/component.js'
            result = render_server.render(path)

            assert result.render() == markup
            requests.post.assert_called_with(
                '/render',
                headers={'content-type': 'application/json'},
                params={'hash': sha.hexdigest()},
                data='{"path": "' + path + '", ''"serializedProps": "{\\"_serverContext\\": '
                     '{\\"location\\": \\"/test\\", '
                     '\\"api_url\\": \\"http://api\\"}}", '
                     '"toStaticMarkup": false}'
            )

    def test_react_render_not_set(self):
        self.flask.config.update({'REACT_RENDER': None})

        with self.flask.test_request_context('/test'):
            result = render_server.render('/widget/component.js')
            assert result.render() == ''
            assert result.get_props() == '{"_serverContext": ' \
                                         '{"location": "/test", ' \
                                         '"api_url": "http://api"}}'

    @patch('react.render_server.requests')
    def test_connection_error(self, requests):
        with self.flask.test_request_context('/test'):
            requests.post.side_effect = ConnectionError()

            with pytest.raises(ConnectionError):
                render_server.render('/path')

    @patch('react.render_server.requests')
    def test_non_200_status_code(self, requests):
        with self.flask.test_request_context('/test'):
            res = Response()
            res.status_code = 400
            requests.post.return_value = res

            with pytest.raises(RenderServerError):
                render_server.render('/path')

    @patch('react.render_server.requests')
    def test_no_markup(self, requests):
        with self.flask.test_request_context('/test'):
            res = Response()
            res.status_code = 200
            res.json = lambda: {'markup': None}
            requests.post.return_value = res

            with pytest.raises(ReactRenderingError):
                render_server.render('/path')

    @patch('react.render_server.requests')
    def test_render_error(self, requests):
        with self.flask.test_request_context('/test'):
            res = Response()
            res.status_code = 200
            res.json = lambda: {'error': 'an error'}
            requests.post.return_value = res

            with pytest.raises(ReactRenderingError):
                render_server.render('/path')
