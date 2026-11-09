"""SQLite 連線與初始化。資料存在 instance/campusfix.sqlite，重開程式後仍會保留。"""
import sqlite3

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

from .constants import ROLE_STAFF, ROLE_STUDENT

# 示範帳號（虛構資料，只供 Demo 使用；README 會列出）
DEMO_USERS = [
    ("student1", "student123", ROLE_STUDENT),
    ("staff1", "staff123", ROLE_STAFF),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """建立資料表並放入示範帳號。注意：會清空既有資料。"""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    db.executemany(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        [(u, generate_password_hash(p), r) for u, p, r in DEMO_USERS],
    )
    db.commit()


@click.command("init-db")
def init_db_command():
    """flask --app app init-db"""
    init_db()
    click.echo("Database initialised with demo accounts.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
