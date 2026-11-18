"""CF-11 See resolution note on resolved reports 的測試（對應測試紀錄 TC-43～TC-46）。

TC-43～TC-45 直接在資料庫插入報修來測詳細頁；TC-46 走完整流程：
學生送出報修 -> staff1 用 CF-13 的 Staff 頁改成 Resolved -> 打開詳細頁。
比對畫面時用 data-field 讀出欄位的值（不綁定 HTML 標籤的寫法）。
"""
from app.db import get_db
from conftest import login
from test_cf8_report_detail import shown_fields


def add_report(app, status, resolution_note=None, updated_at="2026-11-18 14:30:00"):
    """直接在資料庫插入一筆報修（虛構資料），回傳新 ID。"""
    with app.app_context():
        db = get_db()
        cur = db.execute(
            "INSERT INTO reports (title, location, category, description,"
            " status, resolution_note, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("Light flickering", "Library", "Facility", "Ceiling light on 2F flickers.",
             status, resolution_note, updated_at),
        )
        db.commit()
        return cur.lastrowid


def detail_fields(client, report_id):
    """打開詳細頁，回傳頁面上每個 data-field 顯示的值。"""
    resp = client.get(f"/reports/{report_id}")
    assert resp.status_code == 200
    return shown_fields(resp.get_data(as_text=True))


def test_tc43_resolved_report_shows_resolution_note(app, client):
    """AC1：Resolved 的報修，詳細頁顯示處理說明（多行與特殊字元原樣顯示）。"""
    note = "Replaced the light tube.\nChecked other lights on 2F <all OK>."
    report_id = add_report(app, "Resolved", note)

    shown = detail_fields(client, report_id)
    assert shown["status"] == "Resolved"
    assert shown["resolution_note"] == note


def test_tc44_detail_page_shows_last_updated_time(app, client):
    """AC2：詳細頁顯示狀態最後一次更新的時間，不論是哪一種狀態。"""
    for status in ["Submitted", "In Progress", "Resolved"]:
        report_id = add_report(app, status, "Fixed." if status == "Resolved" else None,
                               updated_at="2026-11-19 09:15:00")
        assert detail_fields(client, report_id)["updated_at"] == "2026-11-19 09:15:00", status


def test_tc45_not_resolved_report_has_no_resolution_section(app, client):
    """AC3：不是 Resolved 的報修，不會出現空白的處理說明區塊。

    In Progress 就算資料庫裡有處理說明（CF-13 允許先寫），也不顯示；
    Resolved 但沒有說明的舊資料，也不顯示空白區塊。
    """
    cases = [("Submitted", None), ("In Progress", None),
             ("In Progress", "Waiting for parts"), ("Resolved", None)]
    for status, note in cases:
        report_id = add_report(app, status, note)
        page = client.get(f"/reports/{report_id}").get_data(as_text=True)
        assert "resolution_note" not in shown_fields(page), (status, note)
        assert "Resolution note" not in page, (status, note)


def test_tc46_integration_with_staff_status_update(app, client):
    """整合測試（CF-13 + CF-11）：staff1 把報修改成 Resolved 後，詳細頁顯示說明與更新時間；
    再改回 In Progress，處理說明區塊就消失。"""
    resp = client.post("/reports/new", data={
        "title": "Door stuck", "location": "Building A",
        "category": "Facility", "description": "Main door jams.",
    })
    report_id = int(resp.headers["Location"].rstrip("/").split("/")[-1])

    login(client, "staff1", "staff123")
    client.post(f"/staff/reports/{report_id}/status",
                data={"status": "Resolved", "resolution_note": "Hinge oiled and fixed."})

    with app.app_context():
        row = get_db().execute(
            "SELECT updated_at FROM reports WHERE id = ?", (report_id,)).fetchone()
    shown = detail_fields(client, report_id)
    assert shown["status"] == "Resolved"
    assert shown["resolution_note"] == "Hinge oiled and fixed."
    assert shown["updated_at"] == row["updated_at"]  # 顯示的是 CF-13 存進去的更新時間

    client.post(f"/staff/reports/{report_id}/status",
                data={"status": "In Progress", "resolution_note": "Hinge oiled and fixed."})
    shown = detail_fields(client, report_id)
    assert shown["status"] == "In Progress"
    assert "resolution_note" not in shown
