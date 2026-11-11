"""CF-12 Sign in with a demo account and role 的測試（對應測試紀錄 TC-25～TC-29）。

TC-10 前半（student 與未登入者被拒）在 tests/test_required_cases.py。
示範帳號是虛構資料，建在 app/db.py 的 DEMO_USERS。
"""
from conftest import login


def test_tc25_student_login_shows_role(client):
    """AC2：student1 登入成功 -> 導回列表，導覽列顯示帳號與角色 student。"""
    resp = login(client, "student1", "student123")
    assert resp.status_code == 302  # 登入成功會導向報修列表

    html = client.get("/reports/").get_data(as_text=True)
    assert "student1 (student)" in html
    assert "Log out" in html
    assert ">Staff<" not in html  # student 看不到 Staff 連結（UI 端）


def test_tc26_staff_login_can_open_staff_page(client):
    """AC2/AC3：staff1 登入成功 -> 顯示角色 staff，看得到並進得去 Staff 頁面。"""
    login(client, "staff1", "staff123")
    html = client.get("/reports/").get_data(as_text=True)
    assert "staff1 (staff)" in html
    assert ">Staff<" in html
    assert client.get("/staff/").status_code == 200


def test_tc27_wrong_password_is_rejected(client):
    """AC4：密碼錯誤 -> 顯示錯誤訊息，沒有登入。"""
    resp = login(client, "student1", "wrong-password")
    assert resp.status_code == 401
    assert "Incorrect username or password." in resp.get_data(as_text=True)

    html = client.get("/reports/").get_data(as_text=True)
    assert "Log in" in html and "Log out" not in html


def test_tc28_unknown_username_is_rejected(client):
    """AC4：不存在的帳號 -> 顯示同樣的錯誤訊息，沒有登入。"""
    resp = login(client, "nobody", "student123")
    assert resp.status_code == 401
    assert "Incorrect username or password." in resp.get_data(as_text=True)
    assert client.get("/staff/").status_code == 403


def test_tc29_logout_removes_access(client):
    """AC3：staff 登出後 -> 變回未登入，Staff 頁面再次被拒絕。"""
    login(client, "staff1", "staff123")
    assert client.get("/staff/").status_code == 200

    client.get("/auth/logout")
    assert client.get("/staff/").status_code == 403
    assert "Log in" in client.get("/reports/").get_data(as_text=True)
