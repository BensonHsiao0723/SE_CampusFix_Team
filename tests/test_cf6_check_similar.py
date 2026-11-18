"""CF-6 Check for similar reports before submitting 的測試（對應測試紀錄 TC-47～TC-50）。

只用虛構的測試資料。資料直接插入資料庫，不依賴其他測試檔。
"""
import re

from app.db import get_db

PANEL = 'id="check-existing"'


def insert_report(app, title, location, description="", created_at="2026-11-18 09:00:00"):
    with app.app_context():
        db = get_db()
        cur = db.execute(
            "INSERT INTO reports (title, location, category, description, created_at)"
            " VALUES (?, ?, 'Equipment', ?, ?)",
            (title, location, description or f"{title} details", created_at),
        )
        db.commit()
        return cur.lastrowid


def panel_html(client, **query):
    """打開報修表單頁（可帶 check_q / check_location），只取出「送出前先查」面板的 HTML。"""
    page = client.get("/reports/new", query_string=query).get_data(as_text=True)
    match = re.search(r'<section class="card" id="check-existing">(.*?)</section>', page, flags=re.S)
    assert match, "表單頁要有 Check existing reports first 面板"
    return match.group(1), page


def test_tc47_form_page_has_search_panel(client):
    """AC1：報修表單頁有關鍵字與地點的查詢面板，報修表單本身也還在。"""
    panel, page = panel_html(client)
    assert "Check existing reports first" in panel
    assert 'name="check_q"' in panel
    assert 'name="check_location"' in panel
    assert "All locations" in panel
    # 還沒查詢時，不顯示任何結果訊息
    assert "No matching reports" not in panel
    # 報修表單仍然在
    assert 'name="title"' in page and "Submit report" in page


def test_tc48_matching_reports_are_listed_and_can_be_opened(app, client):
    """AC2：符合的報修列出 ID、title、location、status，並可點進詳細頁；不符合的不出現。"""
    match_id = insert_report(app, "Projector broken", "Library")
    insert_report(app, "Broken chair", "Library")
    insert_report(app, "Projector flickers", "Building A")

    panel, _ = panel_html(client, check_q="projector", check_location="Library")
    assert f'href="/reports/{match_id}"' in panel
    assert f"#{match_id}" in panel
    assert "Projector broken" in panel and "Library" in panel and "Submitted" in panel
    assert "Broken chair" not in panel           # 地點符合但關鍵字不符合
    assert "Projector flickers" not in panel     # 關鍵字符合但地點不符合

    assert client.get(f"/reports/{match_id}").status_code == 200


def test_tc49_no_match_still_allows_new_report(app, client):
    """AC3：沒有符合的報修時顯示提示，學生仍然可以照常送出新報修。"""
    insert_report(app, "Broken chair", "Library")

    panel, page = panel_html(client, check_q="elevator", check_location="")
    assert "No matching reports. You can submit a new report below." in panel
    assert "Submit report" in page

    resp = client.post("/reports/new", data={
        "title": "Elevator stuck", "location": "Building B",
        "category": "Facility", "description": "Stuck on floor 3.",
    })
    assert resp.status_code == 302  # CF-4：送出成功，導向詳細頁
    with app.app_context():
        assert get_db().execute(
            "SELECT COUNT(*) FROM reports WHERE title = 'Elevator stuck'").fetchone()[0] == 1


def test_tc50_uses_same_rules_as_main_search(app, client):
    """AC4：查詢面板和報修列表的搜尋結果完全相同（不分大小寫、title 或 description、AND、% 當一般文字）。"""
    insert_report(app, "WiFi down", "Library", created_at="2026-11-18 09:00:00")
    insert_report(app, "Slow network", "Library", description="The wifi is slow",
                  created_at="2026-11-18 10:00:00")
    insert_report(app, "Battery at 100%", "Building A", created_at="2026-11-18 11:00:00")
    insert_report(app, "Broken chair", "Building A", created_at="2026-11-18 12:00:00")

    def ids(html):
        return re.findall(r'href="/reports/(\d+)"', html)

    for keyword, location in [("WIFI", ""), ("wifi", "Library"), ("wifi", "Building A"),
                              ("100%", ""), ("", "Building A"), ("  chair  ", "")]:
        panel, _ = panel_html(client, check_q=keyword, check_location=location)
        listing = client.get("/reports/", query_string={"q": keyword, "location": location}
                             ).get_data(as_text=True)
        assert ids(panel) == ids(listing), (keyword, location)
