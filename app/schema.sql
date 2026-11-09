-- 資料表草稿：CF-4 的 subtask「Design report data model」請全隊 review 後再定案。
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('student', 'staff'))
);

CREATE TABLE reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,  -- 唯一報修 ID（AUTOINCREMENT 不會重複使用已刪除的 ID）
    title           TEXT    NOT NULL,
    location        TEXT    NOT NULL,
    category        TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'Submitted'
                    CHECK (status IN ('Submitted', 'In Progress', 'Resolved')),
    resolution_note TEXT,
    created_by      INTEGER REFERENCES users(id),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
