"""登入、登出與角色權限。對應 Story CF-12。"""
import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    # TODO CF-12: 依 session["user_id"] 從 users 表讀出使用者，存到 g.user（未登入為 None）
    g.user = None


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # TODO CF-12: 驗證帳密（werkzeug.security.check_password_hash），
        #          成功就把 user_id 存進 session 並導回列表；失敗顯示錯誤訊息
        flash("TODO CF-12: login not implemented yet")
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("reports.list_reports"))


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        # TODO CF-12: 未登入就導向 auth.login
        return view(**kwargs)
    return wrapped


def staff_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        # TODO CF-12: 不是 staff 角色就回傳 403（伺服器端也要擋，不能只靠隱藏按鈕）
        #          ⚠ 目前尚未實作，所有人都能通過 —— TC-10 會驗證這點
        return view(**kwargs)
    return wrapped
