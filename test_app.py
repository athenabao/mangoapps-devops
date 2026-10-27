import re
import sqlite3

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test-only-not-for-deployment",
        "DATABASE": str(tmp_path / "tasks.sqlite3"),
    })


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client):
    response = client.get("/")
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)


def post(client, path, **data):
    return client.post(path, data={"csrf_token": csrf(client), **data})


def test_add_read_complete_delete_and_persist_across_app_restart(app, client):
    assert post(client, "/tasks", title="Verify EC2 deployment").status_code == 303
    assert "Verify EC2 deployment" in client.get("/").text
    with sqlite3.connect(app.config["DATABASE"]) as database:
        task_id = database.execute("SELECT id FROM tasks").fetchone()[0]

    restarted_app = create_app(dict(app.config))
    restarted_client = restarted_app.test_client()
    assert "Verify EC2 deployment" in restarted_client.get("/").text
    assert post(restarted_client, f"/tasks/{task_id}/toggle").status_code == 303
    assert "1 / 1 done" in restarted_client.get("/").text
    assert post(restarted_client, f"/tasks/{task_id}/delete").status_code == 303
    assert "A fresh start." in restarted_client.get("/").text


def test_health_reads_application_table_and_reports_failure(app, client):
    assert client.get("/health").status_code == 200
    assert client.get("/health").json == {"status": "healthy", "app": "ok", "database": "ok"}
    with sqlite3.connect(app.config["DATABASE"]) as database:
        database.execute("DROP TABLE tasks")
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json["database"] == "unavailable"
    assert "no such table" not in response.text


def test_missing_database_is_not_silently_recreated(app, client):
    from pathlib import Path
    Path(app.config["DATABASE"]).unlink()
    assert client.get("/health").status_code == 503
    assert not Path(app.config["DATABASE"]).exists()


def test_csrf_and_invalid_input_are_rejected(client):
    assert client.post("/tasks", data={"title": "No token"}).status_code == 400
    for title in ("", "   ", "a" * 161):
        assert post(client, "/tasks", title=title).status_code == 400
    assert "A fresh start." in client.get("/").text
    assert client.get("/tasks/1/delete").status_code == 405
    assert post(client, "/tasks/999/toggle").status_code == 404


def test_user_input_is_escaped_and_parameterized(client):
    title = "<script>alert(1)</script>'); DROP TABLE tasks;--"
    assert post(client, "/tasks", title=title).status_code == 303
    page = client.get("/")
    assert "<script>" not in page.text
    assert "&lt;script&gt;" in page.text
    assert client.get("/health").status_code == 200
    assert page.headers["X-Content-Type-Options"] == "nosniff"


def test_shared_demo_has_a_task_limit(app, client):
    with sqlite3.connect(app.config["DATABASE"]) as database:
        database.executemany("INSERT INTO tasks (title) VALUES (?)", [("Sample",)] * 500)
    assert post(client, "/tasks", title="Overflow").status_code == 409


def test_malformed_unicode_csrf_token_returns_400(client):
    csrf(client)
    response = client.post("/tasks", data={"title": "Invalid token", "csrf_token": "非ascii"})
    assert response.status_code == 400


def test_production_requires_a_configured_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()
