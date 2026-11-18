"""工作人員端：檢視報修、更新狀態。對應 Story CF-13（權限見 CF-12）。"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .auth import staff_required
from .constants import STATUS_RESOLVED, STATUSES
from .db import get_db

bp = Blueprint("staff", __name__, url_prefix="/staff")

# 錯誤訊息集中放這裡，測試也用同一段文字比對
NOTE_REQUIRED_MESSAGE = "A resolution note is required when the status is Resolved."
INVALID_STATUS_MESSAGE = "Please choose a valid status."


@bp.route("/")
@staff_required  # CF-12：只有 staff 能進來，student／未登入回 403（AC4 伺服器端）
def dashboard():
    """CF-13 AC1：staff 的管理頁，列出所有報修，每筆都有改狀態的表單。"""
    # 和學生的列表一樣，最新的報修排在最前面
    reports = get_db().execute(
        "SELECT id, title, location, status, resolution_note, updated_at"
        " FROM reports ORDER BY created_at DESC, id DESC"
    ).fetchall()
    return render_template("staff/dashboard.html", reports=reports, statuses=STATUSES)


@bp.route("/reports/<int:report_id>/status", methods=["POST"])
@staff_required  # AC4：就算 student 自己送出這個表單，也會在這裡被擋下（403）
def update_status(report_id):
    """CF-13：把一筆報修改成新的狀態，並儲存處理說明（resolution note）。"""
    new_status = request.form.get("status", "")
    note = request.form.get("resolution_note", "").strip()  # 只有空白也算沒填

    db = get_db()
    report = db.execute("SELECT id FROM reports WHERE id = ?", (report_id,)).fetchone()
    if report is None:
        abort(404)  # 要改的報修不存在

    # 狀態只能是固定的三種（Submitted / In Progress / Resolved），防止有人亂送值
    if new_status not in STATUSES:
        flash(INVALID_STATUS_MESSAGE)
        return redirect(url_for("staff.dashboard"))

    # AC2：改成 Resolved 一定要寫處理說明，否則擋下來、什麼都不改
    if new_status == STATUS_RESOLVED and not note:
        flash(f"Report #{report_id}: {NOTE_REQUIRED_MESSAGE}")
        return redirect(url_for("staff.dashboard"))

    # AC3：寫進資料庫並 commit，重新整理或重開程式後都還在
    #      note 沒填就存 NULL；updated_at 記錄這次修改的時間（CF-11 會顯示）
    db.execute(
        "UPDATE reports"
        " SET status = ?, resolution_note = ?, updated_at = datetime('now', 'localtime')"
        " WHERE id = ?",
        (new_status, note or None, report_id),
    )
    db.commit()
    flash(f"Report #{report_id} updated to {new_status}.")
    return redirect(url_for("staff.dashboard"))
