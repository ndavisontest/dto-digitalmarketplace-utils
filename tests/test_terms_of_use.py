from tests.helpers import BaseApplicationTest, Config

from dmutils import terms_of_use


class TestTerms(BaseApplicationTest):

    def setup(self):
        super(TestTerms, self).setup()

        @self.flask.route(terms_of_use.REVIEW_URL)
        def review_terms():
            terms_of_use.set_session_flag(False)
            return 'Here are the new terms of use'

        @self.flask.route(terms_of_use.TERMS_URL)
        def terms():
            return 'Terms terms terms'

        @self.flask.route('/some-page')
        def some_page():
            return 'Interesting content'

        @self.flask.route('/set-flag')
        def set_flag():
            terms_of_use.set_session_flag(True)
            return 'Flag set'

        @self.flask.route('/static/screen.css')
        def static_file():
            return '{}'

    def test_normal_view(self):
        res = self.app.get('/some-page')
        assert res.status_code == 200

    def test_session_flag_set(self):
        res = self.app.get('/set-flag')
        assert res.status_code == 200

        res = self.app.get('/some-page')
        assert res.status_code == 302
        assert res.location.endswith(terms_of_use.REVIEW_URL)

    def test_no_redirect_loop(self):
        res = self.app.get('/set-flag')
        assert res.status_code == 200

        res = self.app.get(terms_of_use.REVIEW_URL)
        assert res.status_code == 200

    def test_viewing_terms(self):
        res = self.app.get('/set-flag')
        assert res.status_code == 200

        res = self.app.get(terms_of_use.TERMS_URL)
        assert res.status_code == 200

    def test_viewing_static_assets(self):
        res = self.app.get('/set-flag')
        assert res.status_code == 200

        res = self.app.get('/static/screen.css')
        assert res.status_code == 200

    def test_full_flow(self):
        res = self.app.get('/set-flag')
        assert res.status_code == 200

        res = self.app.get('/some-page')
        assert res.status_code == 302

        res = self.app.get(res.location)
        assert res.status_code == 200

        res = self.app.get('/some-page')
        assert res.status_code == 200
