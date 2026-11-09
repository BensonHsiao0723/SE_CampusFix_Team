"""骨架本身的基本檢查：確認程式能啟動、頁面能打開、資料庫有建好。"""
from app.db import get_db


def test_home_redirects_to_report_list(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/reports/")


def test_pages_load(client):
    for url in ["/reports/", "/reports/new", "/auth/login"]:
        assert client.get(url).status_code == 200, url


def test_unknown_report_returns_404(client):
    resp = client.get("/reports/9999")
    assert resp.status_code == 404
    assert b"Report not found" in resp.data


def test_init_db_creates_demo_accounts(app):
    with app.app_context():
        roles = {r["username"]: r["role"] for r in get_db().execute("SELECT username, role FROM users")}
    assert roles == {"student1": "student", "staff1": "staff"}
