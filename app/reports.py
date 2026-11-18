"""學生端：送出報修、列表、詳細頁、搜尋。對應 Story CF-4～CF-11。"""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .constants import CATEGORIES, LOCATIONS, STATUS_RESOLVED, STATUS_SUBMITTED
from .db import get_db

bp = Blueprint("reports", __name__, url_prefix="/reports")


def search_reports(keyword="", location=""):
    """CF-9、CF-10 的搜尋規則（CF-6 抽成共用函式，列表頁和報修表單都用這一個）。

    - keyword：比對 title 或 description，不分大小寫；空字串代表不篩選（CF-9）
    - location：地點完全相同才符合；空字串代表 All locations（CF-10）
    - 兩個條件同時使用時取 AND（CF-10 AC2）
    呼叫前請先 strip()。回傳依送出時間由新到舊排序的報修（CF-7）。
    """
    sql = "SELECT id, title, location, category, status, created_at FROM reports"
    params = []
    # CF-10：每個篩選條件各放一個，最後用 AND 接起來，
    #        所以 keyword 和 location 同時使用時，兩個條件都要符合（AC2）
    conditions = []

    # CF-9：有輸入關鍵字才加條件；keyword 已經 strip() 過，只有空白就等於沒輸入，顯示全部（AC3）
    if keyword:
        # % 和 _ 在 LIKE 裡是萬用字元，先在前面加 \ 讓它們變成一般文字，
        # 這樣搜尋 "100%" 只會找到真的含有 "100%" 的報修，而不是全部
        escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"  # 前後加 %：只要「包含」關鍵字就算符合
        # LIKE 對英文字母不分大小寫，所以 wifi / WiFi / WIFI 結果相同（AC2）
        # title 或 description 任一個包含關鍵字就符合（AC1）
        conditions.append("(title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')")
        params += [pattern, pattern]

    # CF-10：有選地點才加條件；地點要完全相同才算符合（AC1）
    if location:
        conditions.append("location = ?")
        params.append(location)

    # CF-10：有任何條件才加 WHERE；兩個條件都有時變成 "... WHERE (關鍵字) AND location = ?"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    # CF-7：最新的排最前面；created_at 只精確到秒，同一秒內再用 id 由大到小排
    sql += " ORDER BY created_at DESC, id DESC"
    # 用 ? 代入使用者輸入，不直接拼進 SQL 字串，避免 SQL injection
    return get_db().execute(sql, params).fetchall()


def validate_choices(form):
    """CF-5：檢查 location 和 category 是否在固定清單內。

    回傳錯誤訊息的 dict，例如 {"location": "..."}；全部正確時回傳空 dict。
    空白的值不在這裡處理，留給 CF-4 的必填檢查，避免同一個欄位出現兩個錯誤訊息。
    """
    errors = {}
    location = form.get("location", "")
    category = form.get("category", "")
    if location and location not in LOCATIONS:
        errors["location"] = "Please choose a location from the list"
    if category and category not in CATEGORIES:
        errors["category"] = "Please choose a category from the list"
    return errors


@bp.route("/new", methods=["GET", "POST"])
def new_report():
    errors = {}
    form = {}
    if request.method == "POST":
        form = request.form
        # CF-4：讀出四個必填欄位，strip() 去掉前後空白（只輸入空白也算沒填）
        title = form.get("title", "").strip()
        location = form.get("location", "").strip()
        category = form.get("category", "").strip()
        description = form.get("description", "").strip()

        # CF-4：每個空白的欄位都給一個「指出是哪個欄位」的錯誤訊息
        if not title:
            errors["title"] = "Title is required"
        if not location:
            errors["location"] = "Location is required"
        if not category:
            errors["category"] = "Category is required"
        if not description:
            errors["description"] = "Description is required"

        # CF-5：location 和 category 必須在固定清單內（用 strip() 後的值檢查，和存進資料庫的值一致）
        errors.update(validate_choices({"location": location, "category": category}))

        # CF-4：沒有任何錯誤才寫進資料庫；有錯就往下走，重新顯示表單和錯誤訊息
        if not errors:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO reports (title, location, category, description, created_by)"
                " VALUES (?, ?, ?, ?, ?)",
                (title, location, category, description,
                 g.user["id"] if g.user else None),
            )
            db.commit()  # 寫進 SQLite 檔案，重新整理或重開程式後資料仍在
            report_id = cursor.lastrowid  # 資料庫自動產生的唯一 ID
            flash(f"Report #{report_id} submitted. Status: {STATUS_SUBMITTED}")
            return redirect(url_for("reports.detail", report_id=report_id))
    # CF-6：表單上方的「送出前先查查看」面板。用 check_q / check_location 當參數名稱，
    #       避免和下面報修表單的 location 欄位混在一起。
    check_q = request.args.get("check_q", "").strip()
    check_location = request.args.get("check_location", "").strip()
    checked = "check_q" in request.args or "check_location" in request.args
    # AC4：和列表頁用同一個 search_reports()，規則完全相同
    similar = search_reports(check_q, check_location) if checked else []
    return render_template(
        "reports/new.html", form=form, errors=errors,
        locations=LOCATIONS, categories=CATEGORIES,
        check_q=check_q, check_location=check_location,
        checked=checked, similar=similar,
    )


@bp.route("/")
def list_reports():
    keyword = request.args.get("q", "").strip()
    # CF-10：下拉選單的 "All locations" 送出的是空字串 ""，代表不篩選地點（AC3）
    location = request.args.get("location", "").strip()
    # CF-7: 每次請求都直接查資料庫，所以新送出的報修不用重開程式就會出現。
    # CF-9、CF-10 的搜尋規則已由 CF-6 抽成 search_reports()（行為不變）
    reports = search_reports(keyword, location)
    return render_template(
        "reports/list.html", reports=reports,
        keyword=keyword, location=location, locations=LOCATIONS,
    )


@bp.route("/lookup")
def lookup():
    """CF-8：依使用者輸入的 ID 跳到詳細頁（AC2）。

    列表上的 ID 顯示成 "#12"，所以輸入時也接受前面帶 "#"。
    """
    raw_id = request.args.get("id", "").strip()
    report_id = raw_id.removeprefix("#").strip()
    if not report_id:
        flash("Please enter a report ID")
        return redirect(url_for("reports.list_reports"))
    if not report_id.isascii() or not report_id.isdigit():
        return report_not_found(raw_id)
    return redirect(url_for("reports.detail", report_id=int(report_id)))


# SQLite INTEGER 的最大值；超過這個數字的 ID 不可能存在，直接當作找不到，
# 避免 sqlite3 綁定參數時 OverflowError 變成 500。
MAX_REPORT_ID = 2**63 - 1


@bp.route("/<int:report_id>")
def detail(report_id):
    """CF-8：顯示單筆報修的所有欄位與目前狀態（AC1、AC4）。

    CF-11：另外顯示最後更新時間；Resolved 的報修再顯示處理說明。
    """
    report = None
    if report_id <= MAX_REPORT_ID:
        report = get_db().execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    if report is None:
        return report_not_found(report_id)
    # CF-11 AC1、AC3：只有「狀態是 Resolved 而且真的有處理說明」才顯示處理說明區塊，
    # 其他狀態（Submitted、In Progress）不會出現空白的處理說明欄位。
    # In Progress 就算有說明也不顯示（PO 授權的設計決定）：Resolved 改回 In Progress 時，
    # CF-13 的表單會沿用舊的說明，若照樣顯示，學生會看到「已修好」的過期說明。
    show_resolution = report["status"] == STATUS_RESOLVED and bool(report["resolution_note"])
    return render_template("reports/detail.html", report=report,
                           show_resolution=show_resolution)


@bp.route("/<path:raw_id>")
def detail_invalid_id(raw_id):
    """CF-8：/reports/abc、/reports/-1 這類不是正整數的 ID，也顯示 Report not found（AC3）。"""
    return report_not_found(raw_id)


def report_not_found(report_id):
    """CF-8 AC3：有導覽列、清楚的 "Report not found" 頁面，回傳 404。"""
    return render_template("reports/not_found.html", report_id=report_id), 404
