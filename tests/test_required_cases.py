"""作業指定的 10 個必測案例（TC-01 ~ TC-10）。

每個測試目前都是 skip。負責該 Story 的組員實作功能後，
把 @pytest.mark.skip 拿掉、寫好測試內容，跑過後把真實結果填進測試紀錄。
"""
import pytest

from app import create_app
from app.db import get_db
from conftest import login  # noqa: F401  (CF-12 完成後會用到)

TODO = pytest.mark.skip(reason="TODO: implement together with the related story")


# ---- CF-4 用的虛構測試資料與小工具 ----
VALID_REPORT = {
    "title": "Projector not working",
    "location": "Building A",
    "category": "Equipment",
    "description": "The projector in room 101 does not turn on.",
}


def count_reports(app):
    """回傳 reports 表目前有幾筆資料。"""
    with app.app_context():
        return get_db().execute("SELECT COUNT(*) FROM reports").fetchone()[0]


def submit(client, data):
    """送出表單，回傳新報修的 ID（從導向的網址 /reports/<id> 取出）。"""
    resp = client.post("/reports/new", data=data)
    assert resp.status_code == 302  # 成功時會導向詳細頁
    return int(resp.headers["Location"].rstrip("/").split("/")[-1])


def test_tc01_valid_report_submission(app, client):
    """CF-4：四個欄位都填寫 -> 儲存成功，顯示 ID 與狀態 Submitted。"""
    resp = client.post("/reports/new", data=VALID_REPORT, follow_redirects=True)

    # 畫面上顯示報修 ID 與狀態 Submitted（驗收條件 3）
    assert resp.status_code == 200
    assert b"Report #1 submitted. Status: Submitted" in resp.data

    # 四個欄位都存進資料庫（驗收條件 1）
    with app.app_context():
        row = get_db().execute("SELECT * FROM reports WHERE id = 1").fetchone()
    for field, value in VALID_REPORT.items():
        assert row[field] == value
    assert row["status"] == "Submitted"


@pytest.mark.parametrize("field, message", [
    ("title", "Title is required"),
    ("location", "Location is required"),
    ("category", "Category is required"),
    ("description", "Description is required"),
])
def test_tc02_missing_required_field(app, client, field, message):
    """CF-4：缺少任一必填欄位 -> 不儲存，顯示該欄位的錯誤訊息。"""
    data = dict(VALID_REPORT, **{field: "   "})  # 只有空白也算沒填
    resp = client.post("/reports/new", data=data)

    assert resp.status_code == 200          # 停在表單頁，沒有導向
    assert message.encode() in resp.data    # 顯示指出欄位的訊息（驗收條件 2）
    assert count_reports(app) == 0          # 沒有存進資料庫


def test_tc03_unique_ids(client):
    """CF-4：送出兩筆報修 -> 兩個 ID 不同。"""
    first_id = submit(client, VALID_REPORT)
    second_id = submit(client, dict(VALID_REPORT, title="Wi-Fi down in library"))
    assert first_id != second_id


def test_tc04_persistence_after_restart(app):
    """CF-4/CF-13：寫入後重新 create_app（指向同一個 DATABASE）-> 資料仍在。"""
    report_id = submit(app.test_client(), VALID_REPORT)

    # 重新整理：同一個程式再讀一次詳細頁
    assert b"Projector not working" in app.test_client().get(f"/reports/{report_id}").data

    # 重新啟動：建立新的 app，指向同一個資料庫檔案（不再 init_db，否則會清空資料）
    restarted = create_app({"TESTING": True, "DATABASE": app.config["DATABASE"]})
    resp = restarted.test_client().get(f"/reports/{report_id}")
    assert resp.status_code == 200
    assert b"Projector not working" in resp.data
    assert b"Submitted" in resp.data


@TODO
def test_tc05_report_details_and_status(client):
    """CF-8：詳細頁內容與送出時一致，狀態正確。"""


@TODO
def test_tc06_keyword_search_case_insensitive(client):
    """CF-9：'wifi' / 'WiFi' / 'WIFI' 結果相同，title 與 description 都會比對。"""


@TODO
def test_tc07_location_filter(client):
    """CF-10：只顯示所選地點；keyword + location 取 AND。"""


@TODO
def test_tc08_search_no_matches(client):
    """CF-9/CF-10：沒有符合的結果 -> 顯示 'No matching reports'。"""


@TODO
def test_tc09_staff_update_requires_resolution_note(client):
    """CF-13：staff 改成 Resolved 但沒填 note -> 被擋；填了 -> 成功。"""


def test_tc10_student_cannot_update_status(app, client):
    """CF-12/CF-13：student 或未登入者 POST 狀態更新 -> 403，資料不變。

    CF-12 負責前半：伺服器端的權限檢查（staff_required）。
    """
    report_id = submit(client, VALID_REPORT)
    update = {"status": "Resolved", "resolution_note": "Fixed"}

    def current_status():
        with app.app_context():
            return get_db().execute(
                "SELECT status FROM reports WHERE id = ?", (report_id,)).fetchone()["status"]

    # 未登入：看 staff 頁面、送出狀態更新都被拒絕
    assert client.get("/staff/").status_code == 403
    assert client.post(f"/staff/reports/{report_id}/status", data=update).status_code == 403

    # student 登入後：一樣被拒絕
    login(client, "student1", "student123")
    assert client.get("/staff/").status_code == 403
    assert client.post(f"/staff/reports/{report_id}/status", data=update).status_code == 403

    # 資料沒有被改
    assert current_status() == "Submitted"
