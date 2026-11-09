import pytest

from app import create_app
from app.db import init_db


@pytest.fixture
def app(tmp_path):
    """每個測試使用一個獨立的暫存資料庫，不會動到 instance/ 裡的 Demo 資料。"""
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    with app.app_context():
        init_db()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password):
    return client.post("/auth/login", data={"username": username, "password": password})
