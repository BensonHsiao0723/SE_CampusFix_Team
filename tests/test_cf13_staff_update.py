"""CF-13 Update report status with resolution note 的測試（對應測試紀錄 TC-30～TC-34）。

TC-09（Resolved 一定要填處理說明）在 tests/test_required_cases.py。
報修用 CF-4 的表單建立，帳號用 app/db.py 的示範帳號（虛構資料）。
"""
from app import create_app
from app.db import get_db
from app.staff import INVALID_STATUS_MESSAGE, NOTE_REQUIRED_MESSAGE
from conftest import login

REPORT = {
    "title": "Air conditioner leaking",
    "location": "Library",
    "category": "Facility",
    "description": "Water drips from the AC on floor 2.",
}


def create_report(client, **changes):
    """用學生的表單送出一筆報修，回傳新 ID。"""
    resp = client.post("/reports/new", data={**REPORT, **changes})
    assert resp.status_code == 302
    return int(resp.headers["Location"].rstrip("/").split("/")[-1])


def saved(app, report_id):
    """直接從資料庫讀出這筆報修的 status、resolution_note、updated_at。"""
    with app.app_context():
        return dict(get_db().execute(
            "SELECT status, resolution_note, updated_at FROM reports WHERE id = ?",
            (report_id,)).fetchone())


def update(client, report_id, status, note=""):
    """以目前登入的身分送出狀態更新，跟著導向回 staff 頁。"""
    return client.post(f"/staff/reports/{report_id}/status",
                       data={"status": status, "resolution_note": note},
                       follow_redirects=True)


def test_tc30_staff_moves_report_through_all_statuses(app, client):
    """AC1：staff 在管理頁把報修 Submitted -> In Progress -> Resolved，學生的詳細頁跟著改變。"""
    report_id = create_report(client)
    login(client, "staff1", "staff123")

    page = client.get("/staff/").get_data(as_text=True)
    assert REPORT["title"] in page
    assert f'action="/staff/reports/{report_id}/status"' in page  # 有這筆報修的更新表單

    resp = update(client, report_id, "In Progress")
    assert f"Report #{report_id} updated to In Progress." in resp.get_data(as_text=True)
    assert saved(app, report_id)["status"] == "In Progress"

    resp = update(client, report_id, "Resolved", "Replaced the drain pipe.")
    assert f"Report #{report_id} updated to Resolved." in resp.get_data(as_text=True)
    assert saved(app, report_id)["status"] == "Resolved"

    detail = client.get(f"/reports/{report_id}").get_data(as_text=True)
    assert 'data-field="status">Resolved<' in detail


def test_tc31_resolved_without_note_is_blocked(app, client):
    """AC2：改成 Resolved 但處理說明空白（或只有空白字元）-> 被擋下，顯示清楚訊息，資料不變。"""
    report_id = create_report(client)
    login(client, "staff1", "staff123")
    update(client, report_id, "In Progress", "Technician assigned.")
    before = saved(app, report_id)

    for empty_note in ["", "   ", "\n\t"]:
        resp = update(client, report_id, "Resolved", empty_note)
        assert NOTE_REQUIRED_MESSAGE in resp.get_data(as_text=True)
        assert saved(app, report_id) == before  # 狀態、說明、更新時間都沒變


def test_tc32_status_and_note_survive_refresh_and_restart(app, client):
    """AC3：狀態與處理說明存進資料庫，重新整理與重新啟動程式後都還在（TC-04 的 CF-13 部分）。"""
    report_id = create_report(client)
    login(client, "staff1", "staff123")
    update(client, report_id, "Resolved", "Fan replaced on 11/18.")

    # 重新整理：再開一次 staff 頁
    page = client.get("/staff/").get_data(as_text=True)
    assert "Fan replaced on 11/18." in page

    # 重新啟動：建立新的 app，指向同一個資料庫檔案（不 init_db，否則會清空）
    restarted = create_app({"TESTING": True, "DATABASE": app.config["DATABASE"]})
    with restarted.app_context():
        row = get_db().execute(
            "SELECT status, resolution_note FROM reports WHERE id = ?", (report_id,)).fetchone()
    assert (row["status"], row["resolution_note"]) == ("Resolved", "Fan replaced on 11/18.")

    new_client = restarted.test_client()
    login(new_client, "staff1", "staff123")
    assert "Fan replaced on 11/18." in new_client.get("/staff/").get_data(as_text=True)


def test_tc33_student_cannot_change_status(app, client):
    """AC4：student 看不到改狀態的地方，自己送出請求也被伺服器拒絕（TC-10 後半）。

    最後用 staff 送出同一個請求會成功，證明前面的 403 是權限擋下的，不是功能沒做。
    """
    report_id = create_report(client)
    request_data = {"status": "Resolved", "resolution_note": "Student tries to close it"}

    login(client, "student1", "student123")
    # UI：導覽列沒有 Staff 連結，詳細頁沒有任何改狀態的表單
    assert ">Staff<" not in client.get("/reports/").get_data(as_text=True)
    detail = client.get(f"/reports/{report_id}").get_data(as_text=True)
    assert "/staff/reports/" not in detail and 'name="status"' not in detail
    # 伺服器：直接 POST 被拒，資料不變
    assert client.post(f"/staff/reports/{report_id}/status", data=request_data).status_code == 403
    assert saved(app, report_id)["status"] == "Submitted"
    assert saved(app, report_id)["resolution_note"] is None

    # 對照組：staff 送出同樣的請求會成功
    client.get("/auth/logout")
    login(client, "staff1", "staff123")
    assert client.post(f"/staff/reports/{report_id}/status", data=request_data).status_code == 302
    assert saved(app, report_id)["status"] == "Resolved"


def test_tc34_invalid_requests_change_nothing(app, client):
    """不合法的狀態值不會被儲存；不存在的報修回 404；成功更新時會記錄 updated_at。"""
    report_id = create_report(client)
    login(client, "staff1", "staff123")
    before = saved(app, report_id)

    for bad_status in ["Closed", "resolved", ""]:
        resp = update(client, report_id, bad_status, "note")
        assert INVALID_STATUS_MESSAGE in resp.get_data(as_text=True)
        assert saved(app, report_id) == before

    assert client.post("/staff/reports/9999/status",
                       data={"status": "In Progress"}).status_code == 404

    # 把 updated_at 改成很久以前，確認更新後會換成現在的時間
    with app.app_context():
        db = get_db()
        db.execute("UPDATE reports SET updated_at = '2000-01-01 00:00:00' WHERE id = ?", (report_id,))
        db.commit()
    update(client, report_id, "In Progress", "  Waiting for parts  ")
    after = saved(app, report_id)
    assert after["updated_at"] > "2000-01-01 00:00:00"
    assert after["resolution_note"] == "Waiting for parts"  # 前後空白會去掉
