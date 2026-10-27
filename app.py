"""A deliberately small EC2 demo: Flask, SQLite, and a real readiness check."""

import hmac
import os
from pathlib import Path
import secrets
import sqlite3

from flask import Flask, abort, g, jsonify, redirect, render_template, request, session, url_for


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    production = os.environ.get("APP_ENV") == "production"
    secret = os.environ.get("SECRET_KEY")
    if production and not secret:
        raise RuntimeError("SECRET_KEY must be configured in production")

    app.config.from_mapping(
        SECRET_KEY=secret or secrets.token_hex(32),
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(app.instance_path) / "tasks.sqlite3")),
        MAX_CONTENT_LENGTH=8192,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Enable after installing HTTPS. HTTP is used for this public demo.
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
    )
    if test_config:
        app.config.update(test_config)

    database_path = Path(app.config["DATABASE"]).resolve()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    app.config["DATABASE"] = str(database_path)
    with sqlite3.connect(database_path, timeout=5) as database:
        database.execute("PRAGMA journal_mode=WAL")
        database.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 160),
                completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            )
        """)

    def get_database():
        if "database" not in g:
            # Do not silently create an empty database if the live file disappears.
            uri = Path(app.config["DATABASE"]).as_uri() + "?mode=rw"
            g.database = sqlite3.connect(uri, uri=True, timeout=5)
            g.database.row_factory = sqlite3.Row
        return g.database

    @app.teardown_appcontext
    def close_database(_error):
        database = g.pop("database", None)
        if database is not None:
            database.close()

    @app.before_request
    def validate_csrf():
        if request.method == "POST":
            expected = session.get("csrf_token")
            supplied = request.form.get("csrf_token", "")
            if not expected or not hmac.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8")):
                abort(400, description="The form expired. Refresh the page and try again.")

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; img-src 'self'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        if not request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        session.setdefault("csrf_token", secrets.token_hex(32))
        tasks = get_database().execute(
            "SELECT id, title, completed, created_at FROM tasks ORDER BY completed, id DESC"
        ).fetchall()
        return render_template(
            "index.html", tasks=tasks,
            completed=sum(task["completed"] for task in tasks),
        )

    @app.post("/tasks")
    def add_task():
        title = request.form.get("title", "").strip()
        if not 1 <= len(title) <= 160:
            abort(400, description="Enter a task between 1 and 160 characters.")
        database = get_database()
        # Keep this shared, unauthenticated demo's data set bounded.
        with database:
            result = database.execute(
                "INSERT INTO tasks (title) SELECT ? WHERE (SELECT COUNT(*) FROM tasks) < 500",
                (title,),
            )
            if result.rowcount == 0:
                abort(409, description="This demo holds 500 tasks. Delete a task to add another.")
        return redirect(url_for("index"), code=303)

    @app.post("/tasks/<int:task_id>/toggle")
    def toggle_task(task_id):
        database = get_database()
        with database:
            result = database.execute(
                "UPDATE tasks SET completed = 1 - completed WHERE id = ?", (task_id,)
            )
            if result.rowcount == 0:
                abort(404)
        return redirect(url_for("index"), code=303)

    @app.post("/tasks/<int:task_id>/delete")
    def delete_task(task_id):
        database = get_database()
        with database:
            result = database.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            if result.rowcount == 0:
                abort(404)
        return redirect(url_for("index"), code=303)

    @app.get("/health")
    def health():
        try:
            # Read the actual application table, rather than returning a static 200.
            get_database().execute("SELECT id FROM tasks LIMIT 1").fetchone()
        except sqlite3.Error:
            app.logger.exception("Database readiness check failed")
            return jsonify(status="unhealthy", app="ok", database="unavailable"), 503
        return jsonify(status="healthy", app="ok", database="ok"), 200

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        app.logger.error("Database request failed", exc_info=error)
        return render_template(
            "error.html", code=503, message="The database is unavailable. Please try again shortly."
        ), 503

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    def request_error(error):
        return render_template("error.html", code=error.code, message=error.description), error.code

    return app
