"""學生端：送出報修、列表、詳細頁、搜尋。對應 Story CF-4～CF-11。"""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .constants import CATEGORIES, LOCATIONS, STATUS_SUBMITTED
from .db import get_db

bp = Blueprint("reports", __name__, url_prefix="/reports")


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

        # TODO CF-5: 檢查 location 和 category 是否在固定清單內

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
    # TODO CF-6 (Sprint 2): 在表單頁提供「先搜尋現有報修」
    return render_template(
        "reports/new.html", form=form, errors=errors,
        locations=LOCATIONS, categories=CATEGORIES,
    )


@bp.route("/")
def list_reports():
    keyword = request.args.get("q", "").strip()
    location = request.args.get("location", "")
    # TODO CF-7: 從資料庫讀出報修，最新的在最前面
    # TODO CF-9 (Sprint 2): keyword 不分大小寫比對 title 或 description
    # TODO CF-10 (Sprint 2): location 篩選，與 keyword 同時使用時取 AND
    reports = []
    return render_template(
        "reports/list.html", reports=reports,
        keyword=keyword, location=location, locations=LOCATIONS,
    )


@bp.route("/lookup")
def lookup():
    """依使用者輸入的 ID 跳到詳細頁。"""
    report_id = request.args.get("id", "").strip()
    if not report_id.isdigit():
        flash("Please enter a numeric report ID")
        return redirect(url_for("reports.list_reports"))
    return redirect(url_for("reports.detail", report_id=int(report_id)))


@bp.route("/<int:report_id>")
def detail(report_id):
    # TODO CF-8: 依 ID 讀出報修；找不到時顯示 "Report not found"（404）
    # TODO CF-11 (Sprint 2): Resolved 的報修要顯示 resolution_note 與 updated_at
    report = get_db().execute(
        "SELECT * FROM reports WHERE id = ?", (report_id,)
    ).fetchone()
    if report is None:
        abort(404, description="Report not found")
    return render_template("reports/detail.html", report=report)
