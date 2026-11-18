"""CF-9 Search reports by keyword 的測試（對應測試紀錄 TC-30～TC-33）。

必測案例 TC-06（不分大小寫）、TC-08（沒有結果）在 test_required_cases.py。
這裡只用虛構的測試資料。
"""
from app.db import get_db
from test_cf7_report_list import add_report


def search(client, keyword):
    """用關鍵字搜尋，回傳列表頁的 HTML 文字。"""
    return client.get("/reports/", query_string={"q": keyword}).get_data(as_text=True)


def test_tc30_matches_title_or_description(app, client):
    """AC1：關鍵字出現在 title 或 description 都算符合；兩邊都沒有的不顯示。"""
    add_report(app, "Projector broken", "2026-11-18 09:00:00")  # description 會是 "Projector broken description"
    # 這筆的 title 沒有 projector，只有 description 有
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO reports (title, location, category, description)"
            " VALUES ('Room 101 issue', 'Library', 'Equipment', 'The projector has no signal')"
        )
        db.commit()
    add_report(app, "Broken chair", "2026-11-18 10:00:00")

    html = search(client, "projector")
    assert "Projector broken" in html   # title 符合
    assert "Room 101 issue" in html     # 只有 description 符合
    assert "Broken chair" not in html   # 都不符合


def test_tc31_spaces_ignored_and_empty_keyword_shows_all(app, client):
    """AC3：前後空白忽略；空白關鍵字（或只有空白）顯示全部。"""
    add_report(app, "Wifi slow", "2026-11-18 09:00:00")
    add_report(app, "Broken chair", "2026-11-18 10:00:00")

    html = search(client, "   wifi   ")
    assert "Wifi slow" in html
    assert "Broken chair" not in html

    for keyword in ["", "    "]:
        html = search(client, keyword)
        assert "Wifi slow" in html and "Broken chair" in html


def test_tc32_two_different_empty_messages(app, client):
    """AC4 + CF-7：沒有任何報修顯示 No reports yet.；有報修但搜尋不到顯示 No matching reports。"""
    html = client.get("/reports/").get_data(as_text=True)
    assert "No reports yet." in html
    assert "No matching reports" not in html

    add_report(app, "Wifi slow", "2026-11-18 09:00:00")
    html = search(client, "elevator")
    assert "No matching reports" in html
    assert "No reports yet." not in html
    assert 'value="elevator"' in html   # 搜尋後關鍵字仍留在搜尋框


def test_tc33_special_characters_are_plain_text(app, client):
    """% 和 _ 當一般文字比對，不會變成「全部符合」的萬用字元。"""
    add_report(app, "Battery at 100% but laptop off", "2026-11-18 09:00:00")
    add_report(app, "Broken chair", "2026-11-18 10:00:00")

    html = search(client, "100%")
    assert "Battery at 100% but laptop off" in html
    assert "Broken chair" not in html

    # 兩筆報修都沒有底線 _，如果 _ 被當成萬用字元（任一字元）就會全部符合
    assert "No matching reports" in search(client, "_")
