"""學生端：送出報修、列表、詳細頁、搜尋。對應 Story CF-4～CF-11。"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .constants import CATEGORIES, LOCATIONS
from .db import get_db

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.route("/new", methods=["GET", "POST"])
def new_report():
    errors = {}
    form = {}
    if request.method == "POST":
        form = request.form
        # TODO CF-4: 檢查 title / location / category / description 四個必填欄位，
        #          有錯就把訊息放進 errors（例如 errors["title"] = "Title is required"）
        # TODO CF-5: 檢查 location 和 category 是否在固定清單內
        # TODO CF-4: 沒有錯誤就 INSERT 到 reports，flash 新的報修 ID，導向詳細頁
        flash("TODO CF-4: saving reports is not implemented yet")
    # TODO CF-6 (Sprint 2): 在表單頁提供「先搜尋現有報修」
    return render_template(
        "reports/new.html", form=form, errors=errors,
        locations=LOCATIONS, categories=CATEGORIES,
    )


@bp.route("/")
def list_reports():
    keyword = request.args.get("q", "").strip()
    location = request.args.get("location", "")
    # CF-7: 每次請求都直接查資料庫，所以新送出的報修不用重開程式就會出現。
    #       created_at 只精確到秒，同一秒內送出的報修再用 id 由大到小排，確保最新的在最前面。
    # TODO CF-9 (Sprint 2): keyword 不分大小寫比對 title 或 description
    # TODO CF-10 (Sprint 2): location 篩選，與 keyword 同時使用時取 AND
    reports = get_db().execute(
        "SELECT id, title, location, category, status, created_at"
        " FROM reports ORDER BY created_at DESC, id DESC"
    ).fetchall()
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
