"""CF-5：地點與分類只能從固定清單選擇（TC-15 ~ TC-19）。

TC-15 ~ TC-17 直接測 validate_choices()，現在就能跑。
TC-18 ~ TC-19 要透過網頁送出報修，必須等 CF-4（儲存報修）合併到 main、
並在 new_report() 呼叫 validate_choices() 之後，才拿掉 skip。
"""
import pytest

from app.constants import CATEGORIES, LOCATIONS
from app.db import get_db
from app.reports import validate_choices

WAIT_FOR_CF4 = pytest.mark.skip(reason="等 CF-4 合併後，new_report() 呼叫 validate_choices() 才能測")


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


@WAIT_FOR_CF4
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


@WAIT_FOR_CF4
def test_tc19_detail_page_shows_selected_choices(client):
    """TC-19：送出合法的報修 -> 詳細頁顯示所選的地點與分類。"""
    resp = client.post("/reports/new", data={
        "title": "Wi-Fi keeps dropping",
        "location": "Dormitory 1",
        "category": "Wi-Fi/Network",
        "description": "Connection drops every few minutes on floor 3.",
    }, follow_redirects=True)
    assert resp.status_code == 200
    # 用 <dd>…</dd> 比對，確定是詳細頁上的值，而不是表單下拉選單裡的選項
    assert b"<dd>Dormitory 1</dd>" in resp.data
    assert b"<dd>Wi-Fi/Network</dd>" in resp.data
