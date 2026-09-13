import tempfile
import unittest
from pathlib import Path

from app import create_app


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = {
            'TESTING': True,
            'SECRET_KEY': 'test',
            'DATABASE': str(Path(self.temp.name) / 'test.sqlite3'),
        }
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as session:
            self.token = session['csrf_token']

    def post(self, url, **data):
        return self.client.post(
            url,
            data={'csrf_token': self.token, **data},
            headers={'HX-Request': 'true'},
        )

    def test_lifecycle_and_persistence(self):
        response = self.post('/tasks', title='最初のタスク')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<!doctype', response.data)
        self.assertIn('最初のタスク', response.get_data(as_text=True))
        persisted = (
            create_app(self.config)
            .test_client()
            .get('/')
            .get_data(as_text=True)
        )
        self.assertIn('最初のタスク', persisted)
        self.assertIn(
            '1 / 1 完了',
            self.post('/tasks/1/toggle').get_data(as_text=True),
        )
        self.assertIn(
            '0 / 1 完了',
            self.post('/tasks/1/toggle').get_data(as_text=True),
        )
        self.assertIn(
            'まだタスクはありません',
            self.post('/tasks/1/delete').get_data(as_text=True),
        )

    def test_validation_csrf_and_escaping(self):
        self.assertEqual(
            self.client.post(
                '/tasks', data={'title': 'blocked'}
            ).status_code,
            400,
        )
        for title in ['   ', 'a' * 201]:
            self.assertIn(
                '1〜200文字',
                self.post('/tasks', title=title).get_data(as_text=True),
            )
        response = self.post('/tasks', title='<script>alert(1)</script>')
        self.assertIn('&lt;script&gt;', response.get_data(as_text=True))
        self.assertEqual(self.post('/tasks/999/toggle').status_code, 404)
        self.assertEqual(self.post('/tasks/999/delete').status_code, 404)

    def test_normal_form_redirects(self):
        response = self.client.post(
            '/tasks',
            data={'csrf_token': self.token, 'title': '通常フォーム'},
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers['Location'], '/')
