"""CF-7 View list of reports 的測試（對應測試紀錄 TC-11～TC-14）。

CF-4（送出報修）還沒完成前，先直接在資料庫插入報修來測試列表。
"""
from app.db import get_db


def add_report(app, title, created_at, location="Library", category="Equipment"):
    with app.app_context():
        db = get_db()
        cur = db.execute(
            "INSERT INTO reports (title, location, category, description, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (title, location, category, f"{title} description", created_at),
        )
        db.commit()
        return cur.lastrowid


def test_tc11_list_shows_required_columns(app, client):
    """AC1：每筆顯示 ID、title、location、category、status、submitted date。"""
    report_id = add_report(app, "Projector broken", "2026-11-11 09:30:00",
                           location="Building A", category="Equipment")
    html = client.get("/reports/").get_data(as_text=True)
    for text in [f"#{report_id}", "Projector broken", "Building A", "Equipment",
                 "Submitted", "2026-11-11 09:30:00"]:
        assert text in html, text


def test_tc12_newest_report_first(app, client):
    """AC2：最新的報修排在最前面（同一秒送出時以較大的 ID 為新）。"""
    add_report(app, "Older report", "2026-11-10 08:00:00")
    add_report(app, "Newer report", "2026-11-11 08:00:00")
    add_report(app, "Same second A", "2026-11-12 08:00:00")
    add_report(app, "Same second B", "2026-11-12 08:00:00")
    html = client.get("/reports/").get_data(as_text=True)
    order = [html.index(t) for t in
             ["Same second B", "Same second A", "Newer report", "Older report"]]
    assert order == sorted(order)


def test_tc13_new_report_appears_without_restart(app, client):
    """AC3：新增報修後，不用重開程式就會出現在列表。"""
    assert "Late report" not in client.get("/reports/").get_data(as_text=True)
    add_report(app, "Late report", "2026-11-11 10:00:00")
    assert "Late report" in client.get("/reports/").get_data(as_text=True)


def test_tc14_empty_list_message(client):
    """AC4：沒有報修時顯示空列表訊息，而不是錯誤。"""
    resp = client.get("/reports/")
    assert resp.status_code == 200
    assert "No reports yet." in resp.get_data(as_text=True)
