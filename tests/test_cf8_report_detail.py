"""CF-8 View report details and current status 的補充測試（對應測試紀錄 TC-20～TC-24）。

TC-05 在 test_required_cases.py。
CF-4（送出報修）還沒完成前，先直接在資料庫插入報修來測試詳細頁。
"""
import html
import re

import pytest

from app.db import get_db

NAV_LINK = 'href="/reports/new"'  # base.html 導覽列的 "Report a problem"


def add_report(app, title="Projector broken", location="Building A",
               category="Equipment", description="The projector does not turn on.",
               status=None, created_at=None):
    """直接在資料庫插入一筆報修，回傳新 ID（未提供的欄位用資料表預設值）。"""
    columns = {"title": title, "location": location,
               "category": category, "description": description}
    if status is not None:
        columns["status"] = status
    if created_at is not None:
        columns["created_at"] = created_at
    with app.app_context():
        db = get_db()
        cur = db.execute(
            f"INSERT INTO reports ({', '.join(columns)})"
            f" VALUES ({', '.join('?' for _ in columns)})",
            tuple(columns.values()),
        )
        db.commit()
        return cur.lastrowid


def get_report_row(app, report_id):
    with app.app_context():
        return dict(get_db().execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone())


def shown_fields(page_html):
    """取出詳細頁上每個 data-field 實際顯示的文字（已還原 HTML escape）。"""
    return {name: html.unescape(value) for name, value in
            re.findall(r'data-field="(\w+)">(.*?)</', page_html, flags=re.S)}


def assert_not_found_page(resp):
    page = resp.get_data(as_text=True)
    assert resp.status_code == 404
    assert "Report not found" in page
    assert NAV_LINK in page, "Report not found 頁面要保留網站導覽列"


def test_tc20_unknown_id_shows_report_not_found(client):
    """AC3：開啟不存在的 ID -> 404，有導覽列的 "Report not found" 頁面並顯示該 ID。"""
    resp = client.get("/reports/9999")
    assert_not_found_page(resp)
    assert "9999" in resp.get_data(as_text=True)


def test_tc21_open_report_from_list(app, client):
    """AC2：從列表點報修 ID 的連結 -> 進到該筆的詳細頁。"""
    report_id = add_report(app, title="Broken window")
    list_html = client.get("/reports/").get_data(as_text=True)
    link = f'href="/reports/{report_id}"'
    if link not in list_html:
        pytest.skip("列表尚未顯示報修（CF-7 合併到 main 後此測試才會執行）")
    resp = client.get(f"/reports/{report_id}")
    assert resp.status_code == 200
    assert shown_fields(resp.get_data(as_text=True))["title"] == "Broken window"


@pytest.mark.parametrize("typed", ["{id}", "  {id}  ", "#{id}"])
def test_tc22_open_report_by_entering_id(app, client, typed):
    """AC2：在「Open report by ID」輸入 ID（可含空白或列表上的 #）-> 導向該筆詳細頁。"""
    report_id = add_report(app, title="Water leak")
    resp = client.get("/reports/lookup", query_string={"id": typed.format(id=report_id)})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/reports/{report_id}")
    page = client.get(resp.headers["Location"]).get_data(as_text=True)
    assert shown_fields(page)["title"] == "Water leak"


def test_tc23_lookup_unknown_or_invalid_id(client):
    """AC3：輸入不存在或不是數字的 ID -> 清楚的 "Report not found"；空白 -> 提示輸入 ID。"""
    resp = client.get("/reports/lookup", query_string={"id": "424242"}, follow_redirects=True)
    assert_not_found_page(resp)

    for typed in ["abc", "12abc", "1.5", "-3", "１２"]:  # 最後一個是全形數字
        resp = client.get("/reports/lookup", query_string={"id": typed})
        assert_not_found_page(resp)

    resp = client.get("/reports/lookup", query_string={"id": "   "}, follow_redirects=True)
    assert resp.status_code == 200
    assert "Please enter a report ID" in resp.get_data(as_text=True)


@pytest.mark.parametrize("path", ["abc", "-1", "0", "1.5", "99999999999999999999999"])
def test_tc24_invalid_id_in_url(client, path):
    """AC3：網址裡的 ID 不是有效的正整數（含超過 SQLite 上限）-> 404 Report not found，不會 500。"""
    assert_not_found_page(client.get(f"/reports/{path}"))
