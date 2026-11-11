"""學生端：送出報修、列表、詳細頁、搜尋。對應 Story CF-4～CF-11。"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

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
    """CF-8：顯示單筆報修的所有欄位與目前狀態（AC1、AC4）。"""
    # TODO CF-11 (Sprint 2): Resolved 的報修要顯示 resolution_note 與 updated_at
    report = None
    if report_id <= MAX_REPORT_ID:
        report = get_db().execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    if report is None:
        return report_not_found(report_id)
    return render_template("reports/detail.html", report=report)


@bp.route("/<path:raw_id>")
def detail_invalid_id(raw_id):
    """CF-8：/reports/abc、/reports/-1 這類不是正整數的 ID，也顯示 Report not found（AC3）。"""
    return report_not_found(raw_id)


def report_not_found(report_id):
    """CF-8 AC3：有導覽列、清楚的 "Report not found" 頁面，回傳 404。"""
    return render_template("reports/not_found.html", report_id=report_id), 404
