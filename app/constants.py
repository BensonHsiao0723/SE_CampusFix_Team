"""固定選項。CF-5 會用到這些清單；全隊確認後可再增減。"""

LOCATIONS = [
    "Building A",
    "Building B",
    "Library",
    "Student Center",
    "Dormitory 1",
    "Sports Hall",
]

CATEGORIES = ["Equipment", "Facility", "Wi-Fi/Network", "Other"]

# 應用程式內的報修狀態（不是 Jira 的 To Do / In Progress / Done）
STATUS_SUBMITTED = "Submitted"
STATUS_IN_PROGRESS = "In Progress"
STATUS_RESOLVED = "Resolved"
STATUSES = [STATUS_SUBMITTED, STATUS_IN_PROGRESS, STATUS_RESOLVED]

ROLE_STUDENT = "student"
ROLE_STAFF = "staff"
