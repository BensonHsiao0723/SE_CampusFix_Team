"""登入、登出與角色權限。對應 Story CF-12。"""
import functools

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .constants import ROLE_STAFF
from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    """每個請求開始前執行：依 session 裡的 user_id 找出目前登入的使用者。"""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None  # 沒登入
    else:
        # g.user 是一列資料，可以用 g.user["username"]、g.user["role"] 取值
        g.user = get_db().execute(
            "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        # 帳號不存在或密碼錯誤都顯示同一個訊息，不透露是哪一個錯（驗收條件 4）
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect username or password.")
            return render_template("auth/login.html"), 401

        # 登入成功：先清掉舊的 session，再記住這個使用者的 id
        session.clear()
        session["user_id"] = user["id"]
        flash(f"Signed in as {user['username']} ({user['role']}).")  # 顯示角色（驗收條件 2）
        return redirect(url_for("reports.list_reports"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("reports.list_reports"))


def login_required(view):
    """裝飾器：沒登入的人會被導向登入頁。"""
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped


def staff_required(view):
    """裝飾器：只有 staff 角色能進入，其他人（student、未登入）回傳 403 Forbidden。

    這是伺服器端的檢查（驗收條件 3）：就算有人自己打網址或送出表單也會被擋，
    不是只靠 base.html 把 Staff 連結藏起來。
    """
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None or g.user["role"] != ROLE_STAFF:
            abort(403)
        return view(**kwargs)
    return wrapped
