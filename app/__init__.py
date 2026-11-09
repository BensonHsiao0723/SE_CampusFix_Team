"""CampusFix Flask 應用程式（application factory）。"""
import os

from flask import Flask, redirect, url_for


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

    return app
