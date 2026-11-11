"""CF-5：地點與分類只能從固定清單選擇（TC-15 ~ TC-19）。

TC-15 ~ TC-17 直接測 validate_choices() 這個函式。
TC-18 ~ TC-19 透過網頁送出報修，測 new_report() 真的有用到 validate_choices()
（需要 CF-4 的儲存功能，CF-4 已合併到 main）。
"""
from app.constants import CATEGORIES, LOCATIONS
from app.db import get_db
from app.reports import validate_choices


def test_tc15_values_from_lists_are_accepted():
    """TC-15：清單裡的每個地點、每個分類都會通過檢查。"""
    for location in LOCATIONS:
        for category in CATEGORIES:
            form = {"location": location, "category": category}
            assert validate_choices(form) == {}, form


def test_tc16_location_outside_list_is_rejected():
    """TC-16：不在清單內的地點會得到錯誤訊息（大小寫不同也算不在清單內）。"""
    for bad_location in ["Building Z", "library", "<script>"]:
        errors = validate_choices({"location": bad_location, "category": "Other"})
        assert errors == {"location": "Please choose a location from the list"}, bad_location


def test_tc17_category_outside_list_is_rejected():
    """TC-17：不在清單內的分類會得到錯誤訊息；兩個都錯時兩個欄位都有訊息。"""
    errors = validate_choices({"location": "Library", "category": "Plumbing"})
    assert errors == {"category": "Please choose a category from the list"}

    errors = validate_choices({"location": "Mars Base", "category": "Plumbing"})
    assert set(errors) == {"location", "category"}


def test_tc18_server_rejects_value_outside_list(client, app):
    """TC-18：直接 POST 清單外的值 -> 不儲存，頁面顯示錯誤訊息。"""
    resp = client.post("/reports/new", data={
        "title": "Projector broken",
        "location": "Building Z",
        "category": "Equipment",
        "description": "The projector does not turn on.",
    })
    assert b"Please choose a location from the list" in resp.data
    with app.app_context():
        count = get_db().execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    assert count == 0


def test_tc19_detail_page_shows_selected_choices(client):
    """TC-19：送出合法的報修 -> 詳細頁顯示所選的地點與分類。"""
    resp = client.post("/reports/new", data={
        "title": "Wi-Fi keeps dropping",
        "location": "Dormitory 1",
        "category": "Wi-Fi/Network",
        "description": "Connection drops every few minutes on floor 3.",
    }, follow_redirects=True)
    assert resp.status_code == 200
    # 比對詳細頁上 location / category 欄位的值，而不是表單下拉選單裡的選項
    # （CF-8 審查時調整：不綁定 <dd> 的確切寫法，詳細頁版型改了也不會誤判）
    from test_cf8_report_detail import shown_fields
    shown = shown_fields(resp.get_data(as_text=True))
    assert shown["location"] == "Dormitory 1"
    assert shown["category"] == "Wi-Fi/Network"
