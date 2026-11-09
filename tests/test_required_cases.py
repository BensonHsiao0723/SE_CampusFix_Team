"""作業指定的 10 個必測案例（TC-01 ~ TC-10）。

每個測試目前都是 skip。負責該 Story 的組員實作功能後，
把 @pytest.mark.skip 拿掉、寫好測試內容，跑過後把真實結果填進測試紀錄。
"""
import pytest

from conftest import login  # noqa: F401  (CF-12 完成後會用到)

TODO = pytest.mark.skip(reason="TODO: implement together with the related story")


@TODO
def test_tc01_valid_report_submission(client):
    """CF-4：四個欄位都填寫 -> 儲存成功，顯示 ID 與狀態 Submitted。"""


@TODO
def test_tc02_missing_required_field(client):
    """CF-4：缺少任一必填欄位 -> 不儲存，顯示該欄位的錯誤訊息。"""


@TODO
def test_tc03_unique_ids(client):
    """CF-4：送出兩筆報修 -> 兩個 ID 不同。"""


@TODO
def test_tc04_persistence_after_restart(app):
    """CF-4/CF-13：寫入後重新 create_app（指向同一個 DATABASE）-> 資料仍在。"""


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


@TODO
def test_tc10_student_cannot_update_status(client):
    """CF-12/CF-13：student 或未登入者 POST 狀態更新 -> 403，資料不變。"""
