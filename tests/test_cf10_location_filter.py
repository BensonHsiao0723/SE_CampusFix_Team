"""CF-10 Filter reports by location (combined with keyword) 的測試。

必測案例 TC-07（地點篩選、keyword + location 取 AND）與 TC-08 的地點部分
在 test_required_cases.py。這裡只用虛構的測試資料。
"""
from test_cf7_report_list import add_report


def list_page(client, keyword="", location=""):
    """用關鍵字和地點查詢列表，回傳 HTML 文字。"""
    return client.get(
        "/reports/", query_string={"q": keyword, "location": location}
    ).get_data(as_text=True)


def add_sample_reports(app):
    """三筆虛構報修：兩筆在 Library、一筆在 Building A；兩筆含 wifi。

    add_report() 會把 description 設成「title + description」。
    """
    add_report(app, "Wifi slow", "2026-11-18 09:00:00", location="Library")
    add_report(app, "Wifi down", "2026-11-18 10:00:00", location="Building A")
    add_report(app, "Broken chair", "2026-11-18 11:00:00", location="Library")


def test_cf10_only_selected_location_is_shown(app, client):
    """AC1：選了地點，只顯示該地點的報修。"""
    add_sample_reports(app)

    html = list_page(client, location="Library")
    assert "Wifi slow" in html
    assert "Broken chair" in html
    assert "Wifi down" not in html      # Building A 的不顯示

    html = list_page(client, location="Building A")
    assert "Wifi down" in html
    assert "Wifi slow" not in html and "Broken chair" not in html


def test_cf10_keyword_and_location_must_both_match(app, client):
    """AC2：keyword 和 location 同時使用時取 AND，兩個條件都要符合。"""
    add_sample_reports(app)

    html = list_page(client, keyword="wifi", location="Library")
    assert "Wifi slow" in html          # 含 wifi 且在 Library -> 顯示
    assert "Wifi down" not in html      # 含 wifi 但在 Building A -> 不顯示
    assert "Broken chair" not in html   # 在 Library 但不含 wifi -> 不顯示


def test_cf10_all_locations_removes_location_filter(app, client):
    """AC3：選 All locations（送出空字串）就不篩選地點。"""
    add_sample_reports(app)

    html = list_page(client, location="")
    for title in ["Wifi slow", "Wifi down", "Broken chair"]:
        assert title in html

    # 只剩關鍵字條件：兩個地點含 wifi 的都會出現
    html = list_page(client, keyword="wifi", location="")
    assert "Wifi slow" in html and "Wifi down" in html
    assert "Broken chair" not in html


def test_cf10_keyword_and_location_stay_visible(app, client):
    """AC4：結果出來後，搜尋框仍是剛輸入的關鍵字，下拉選單仍選著剛選的地點。"""
    add_sample_reports(app)

    html = list_page(client, keyword="wifi", location="Library")
    assert 'value="wifi"' in html
    assert "<option selected>Library</option>" in html
    assert "<option selected>Building A</option>" not in html

    # 選 All locations 時，沒有任何地點被選取
    html = list_page(client, keyword="wifi", location="")
    assert "<option selected>" not in html


def test_cf10_no_match_shows_message(app, client):
    """沒有符合的結果時顯示 No matching reports（不是 CF-7 的 No reports yet.）。"""
    add_sample_reports(app)

    for keyword, location in [("", "Sports Hall"), ("chair", "Building A")]:
        html = list_page(client, keyword=keyword, location=location)
        assert "No matching reports" in html
        assert "No reports yet." not in html
