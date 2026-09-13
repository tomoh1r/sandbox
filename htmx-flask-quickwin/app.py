import os
import secrets
import sqlite3
from pathlib import Path

from flask import (
    Flask,
    abort,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
        DATABASE=str(Path(app.instance_path) / 'tasks.sqlite3'),
        MAX_CONTENT_LENGTH=16 * 1024,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(error=None):
        connection = g.pop('db', None)
        if connection is not None:
            connection.close()

    with app.app_context():
        db().execute(
            'CREATE TABLE IF NOT EXISTS tasks ('
            'id INTEGER PRIMARY KEY, '
            'title TEXT NOT NULL, '
            'done INTEGER NOT NULL DEFAULT 0)'
        )
        db().commit()

    @app.before_request
    def csrf_protection():
        session.setdefault('csrf_token', secrets.token_hex(32))
        if request.method == 'POST':
            token = request.form.get('csrf_token', '')
            if not secrets.compare_digest(token, session['csrf_token']):
                abort(
                    400,
                    description='ページを再読み込みして、もう一度お試しください。',
                )

    def page(error=None, title=''):
        tasks = db().execute('SELECT * FROM tasks ORDER BY done, id DESC').fetchall()
        template = (
            'partials/tasks.html'
            if request.headers.get('HX-Request') == 'true'
            else 'index.html'
        )
        return render_template(template, tasks=tasks, error=error, title=title)

    def updated():
        if request.headers.get('HX-Request') == 'true':
            return page()
        return redirect(url_for('index'), code=303)

    @app.get('/')
    def index():
        return page()

    @app.post('/tasks')
    def add_task():
        title = request.form.get('title', '').strip()
        if not 1 <= len(title) <= 200:
            return page(
                'タスクを1〜200文字で入力してください。', title
            )
        db().execute('INSERT INTO tasks (title) VALUES (?)', (title,))
        db().commit()
        return updated()

    @app.post('/tasks/<int:task_id>/toggle')
    def toggle_task(task_id):
        result = db().execute(
            'UPDATE tasks SET done = 1 - done WHERE id = ?',
            (task_id,),
        )
        if result.rowcount == 0:
            abort(404)
        db().commit()
        return updated()

    @app.post('/tasks/<int:task_id>/delete')
    def delete_task(task_id):
        result = db().execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        if result.rowcount == 0:
            abort(404)
        db().commit()
        return updated()

    return app
