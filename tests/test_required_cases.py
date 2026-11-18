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


def test_tc05_report_details_and_status(app, client):
    """CF-8：詳細頁內容與送出時一致，狀態正確。

    透過送出表單（CF-4）建立報修；內容刻意包含 HTML 特殊字元、引號、
    中文與換行，確認詳細頁顯示的文字和送出的完全相同（AC1、AC4）。
    """
    from test_cf8_report_detail import get_report_row, shown_fields

    submitted = {
        "title": 'Projector <b>broken</b> & "flickering"',
        "location": "Library",
        "category": "Equipment",
        "description": "第一行：投影機不亮\nSecond line: it's been 3 days <script>x</script>",
    }
    report_id = submit(client, submitted)
    saved = get_report_row(app, report_id)

    resp = client.get(f"/reports/{report_id}")
    assert resp.status_code == 200
    shown = shown_fields(resp.get_data(as_text=True))
    # CF-11 起詳細頁多顯示最後更新時間（updated_at）
    assert shown == {**submitted, "status": "Submitted", "created_at": saved["created_at"],
                     "updated_at": saved["updated_at"]}

    # 狀態改變後，詳細頁顯示的是目前狀態
    with app.app_context():
        db = get_db()
        db.execute("UPDATE reports SET status = 'In Progress' WHERE id = ?", (report_id,))
        db.commit()
    shown = shown_fields(client.get(f"/reports/{report_id}").get_data(as_text=True))
    assert shown["status"] == "In Progress"


def test_tc06_keyword_search_case_insensitive(client):
    """CF-9：'wifi' / 'WiFi' / 'WIFI' 結果相同，title 與 description 都會比對。"""
    submit(client, dict(VALID_REPORT, title="WiFi not working"))              # title 有 WiFi
    submit(client, dict(VALID_REPORT, title="Slow internet",
                        description="The wifi in the library drops often."))  # 只有 description 有 wifi
    submit(client, dict(VALID_REPORT, title="Broken chair",
                        description="A leg of the chair is broken."))          # 都沒有

    results = []
    for keyword in ["wifi", "WiFi", "WIFI"]:
        html = client.get("/reports/", query_string={"q": keyword}).get_data(as_text=True)
        assert "WiFi not working" in html
        assert "Slow internet" in html
        assert "Broken chair" not in html
        results.append([t for t in ["WiFi not working", "Slow internet", "Broken chair"] if t in html])
    assert results[0] == results[1] == results[2]  # 三種寫法結果完全相同


def test_tc07_location_filter(client):
    """CF-10：只顯示所選地點；keyword + location 取 AND。"""
    submit(client, dict(VALID_REPORT, title="Library wifi", location="Library",
                        description="The wifi is slow."))
    submit(client, dict(VALID_REPORT, title="Library chair", location="Library",
                        description="A chair is broken."))
    submit(client, dict(VALID_REPORT, title="Building A wifi", location="Building A",
                        description="No wifi signal."))

    def shown(**query):
        html = client.get("/reports/", query_string=query).get_data(as_text=True)
        return [t for t in ["Library wifi", "Library chair", "Building A wifi"] if t in html]

    # 只選地點：只顯示該地點的報修
    assert shown(location="Library") == ["Library wifi", "Library chair"]
    # 關鍵字 + 地點：兩個都要符合（AND）
    assert shown(q="wifi", location="Library") == ["Library wifi"]
    # All locations（空字串）：不篩選地點
    assert shown(q="wifi", location="") == ["Library wifi", "Building A wifi"]


def test_tc08_search_no_matches(client):
    """CF-9/CF-10：沒有符合的結果 -> 顯示 'No matching reports'。

    CF-9 負責關鍵字的部分；地點的部分由 CF-10 補上。
    """
    submit(client, VALID_REPORT)  # 有一筆報修，但不含 elevator
    html = client.get("/reports/", query_string={"q": "elevator"}).get_data(as_text=True)
    assert "No matching reports" in html
    assert "Projector not working" not in html

    # CF-10：VALID_REPORT 在 Building A
    # 地點沒有符合
    html = client.get("/reports/", query_string={"location": "Library"}).get_data(as_text=True)
    assert "No matching reports" in html
    # 關鍵字和地點各自有符合的報修，但沒有同時符合的（AND）
    html = client.get("/reports/", query_string={"q": "projector", "location": "Library"}).get_data(as_text=True)
    assert "No matching reports" in html
    assert "Projector not working" not in html


def test_tc09_staff_update_requires_resolution_note(app, client):
    """CF-13：staff 改成 Resolved 但沒填 note -> 被擋；填了 -> 成功。"""
    report_id = submit(client, VALID_REPORT)
    login(client, "staff1", "staff123")
    url = f"/staff/reports/{report_id}/status"

    def current():
        with app.app_context():
            row = get_db().execute(
                "SELECT status, resolution_note FROM reports WHERE id = ?", (report_id,)).fetchone()
        return row["status"], row["resolution_note"]

    # 沒填處理說明 -> 被擋下，顯示清楚的訊息，資料不變
    resp = client.post(url, data={"status": "Resolved", "resolution_note": ""},
                       follow_redirects=True)
    assert b"A resolution note is required when the status is Resolved." in resp.data
    assert current() == ("Submitted", None)

    # 填了處理說明 -> 成功，狀態變 Resolved，說明也存起來
    resp = client.post(url, data={"status": "Resolved", "resolution_note": "Projector replaced."},
                       follow_redirects=True)
    assert f"Report #{report_id} updated to Resolved.".encode() in resp.data
    assert current() == ("Resolved", "Projector replaced.")


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
