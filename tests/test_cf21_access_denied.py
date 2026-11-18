"""CF-21 Show a friendly access-denied page 的測試（對應測試紀錄 TC-30～TC-33）。

CF-12 的權限檢查（staff_required）已經會回傳 403；
CF-21 只改變被擋下時「看到的頁面」，所以也要確認 CF-12 的行為沒有被改壞。
"""
from app.db import get_db
from conftest import login

NAV_LINK = 'href="/reports/new"'  # base.html 導覽列的 "Report a problem"


def test_tc30_signed_out_user_sees_friendly_page(client):
    """AC1/AC2/AC3：未登入開 staff 頁 -> 403，有導覽列、說明只有 staff 能進，並提供 Log in 與回列表的連結。"""
    resp = client.get("/staff/")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 403
    assert "Access denied" in html
    assert "only available to <strong>staff</strong>" in html
    assert NAV_LINK in html, "要保留網站導覽列"
    assert 'href="/auth/login"' in html
    assert 'href="/reports/"' in html
    assert "Forbidden" not in html  # 不再是 Flask 預設頁面


def test_tc31_student_sees_who_is_signed_in(client):
    """AC1/AC2：student 開 staff 頁 -> 403，頁面說明目前登入的是 student，並提供 Log out 的連結。"""
    login(client, "student1", "student123")
    resp = client.get("/staff/")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 403
    assert "signed in as <strong>student1</strong> (student)" in html
    assert 'href="/auth/logout"' in html
    assert "Staff: manage reports" not in html  # 沒有顯示任何 staff 頁面內容


def test_tc32_student_status_update_is_still_rejected(app, client):
    """AC3：student 直接送出狀態更新 -> 403 友善頁面，資料庫中的報修完全沒變。"""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO reports (title, location, category, description)"
            " VALUES ('Broken chair', 'Library', 'Facility', 'Leg is loose')"
        )
        db.commit()
        before = dict(db.execute("SELECT * FROM reports WHERE id = 1").fetchone())

    login(client, "student1", "student123")
    resp = client.post("/staff/reports/1/status",
                       data={"status": "Resolved", "resolution_note": "fixed"})
    assert resp.status_code == 403
    assert "Access denied" in resp.get_data(as_text=True)

    with app.app_context():
        after = dict(get_db().execute("SELECT * FROM reports WHERE id = 1").fetchone())
    assert after == before


def test_tc33_staff_can_still_open_staff_page(client):
    """AC4：staff 仍然可以正常進入 staff 頁（CF-12 的行為沒有被改壞）。"""
    login(client, "staff1", "staff123")
    resp = client.get("/staff/")
    assert resp.status_code == 200
    assert "Access denied" not in resp.get_data(as_text=True)
