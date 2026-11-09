"""工作人員端：檢視報修、更新狀態。對應 Story CF-13（權限見 CF-12）。"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import staff_required
from .constants import STATUSES

bp = Blueprint("staff", __name__, url_prefix="/staff")


@bp.route("/")
@staff_required
def dashboard():
    # TODO CF-13: 列出所有報修，讓 staff 選擇要處理的報修
    reports = []
    return render_template("staff/dashboard.html", reports=reports, statuses=STATUSES)


@bp.route("/reports/<int:report_id>/status", methods=["POST"])
@staff_required
def update_status(report_id):
    new_status = request.form.get("status", "")
    note = request.form.get("resolution_note", "").strip()
    # TODO CF-13: 檢查 new_status 是否合法；
    #           改成 Resolved 時 note 不可空白，否則顯示錯誤；
    #           UPDATE status、resolution_note、updated_at
    flash("TODO CF-13: status update not implemented yet")
    return redirect(url_for("staff.dashboard"))
