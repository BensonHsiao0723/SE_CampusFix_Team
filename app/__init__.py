"""CampusFix Flask 應用程式（application factory）。"""
import os

from flask import Flask, redirect, render_template, url_for


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # Demo 用的預設值；正式環境請用環境變數 SECRET_KEY 覆蓋
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "campusfix.sqlite"),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    from . import auth, db, reports, staff

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(staff.bp)

    @app.route("/")
    def index():
        return redirect(url_for("reports.list_reports"))

    @app.errorhandler(403)
    def access_denied(error):
        """CF-21：被 staff_required 擋下時，顯示有導覽列的說明頁，而不是 Flask 預設的 Forbidden 頁。

        仍然回傳 403（驗收條件 3），頁面上不放任何 staff 才看得到的資料。
        """
        return render_template("errors/403.html"), 403

    return app
