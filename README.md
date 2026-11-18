# CampusFix

A small web application where students report campus problems (broken equipment, damaged facilities,
Wi-Fi failures, ...) and staff record progress until each report is resolved.
Built with Python, Flask and SQLite for the NTPU Software Engineering course (CampusFix Agile Team Project with Jira).

- **GitHub:** https://github.com/BensonHsiao0723/SE_CampusFix_Team
- **Jira (project CF):** https://gm-team-ih1ltuvt.atlassian.net/jira/software/projects/CF/boards/2
- **Confluence (DoD, reviews, retrospectives, test record):** https://gm-team-ih1ltuvt.atlassian.net/wiki/spaces/C/overview

## Features

| Capability | What the app does | Jira |
|---|---|---|
| Report a problem | Form with title, location, category and description; every field is required and location / category must come from fixed lists | CF-4, CF-5 |
| Check before reporting | "Check existing reports first" panel on the form searches existing reports with the same rules as the report list | CF-6 |
| Confirm and track | Unique report ID, report list (newest first), detail page with current status and last updated time, open a report by ID, clear "Report not found" page | CF-7, CF-8, CF-11 |
| Search existing reports | Case-insensitive keyword search in title or description, location filter, combined with AND | CF-9, CF-10 |
| Manage resolution | Staff view to change status (Submitted, In Progress, Resolved); a resolution note is required when resolving; students see the note on resolved reports | CF-13, CF-11 |
| Access control | Predefined demo accounts; only the staff role can open staff pages or update reports; others see an "Access denied" page | CF-12, CF-21 |
| Preserve data | Reports and updates are stored in SQLite and survive page refresh and application restart | CF-4, CF-13 |

## Requirements

- Python 3.10 or newer (tested with 3.14)
- Windows: use `py`; macOS/Linux: use `python3`

## Setup (first time)

```bash
git clone https://github.com/BensonHsiao0723/SE_CampusFix_Team.git
cd SE_CampusFix_Team
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask --app app init-db
```

macOS/Linux: `python3 -m venv .venv` and `source .venv/bin/activate`.

`init-db` creates `instance/campusfix.sqlite` and the demo accounts.
**It deletes all existing data**, so run it only once, or again when you want a clean demo.

## Run

```bash
flask --app app run
```

Open http://127.0.0.1:5000

Data is stored in `instance/campusfix.sqlite`, so it survives page refreshes and application restarts
(stop the server with Ctrl+C and start it again to check).

## Demo accounts

Fictional accounts for demonstration only (no real personal data is used anywhere in this project):

| Role    | Username   | Password     | Can do |
|---------|------------|--------------|--------|
| Student | `student1` | `student123` | Submit, list, search and open reports |
| Staff   | `staff1`   | `staff123`   | Everything above, plus the **Staff** page to update status |

Submitting and viewing reports does not require signing in; the staff page does.

## Behaviour notes

**Search (CF-9, CF-10, CF-6)**
- The keyword matches the title **or** the description, ignoring letter case (English letters) and leading/trailing spaces.
- `%` and `_` are treated as normal characters.
- When a keyword and a location are both given, a report must match **both** (AND).
- An empty keyword or "All locations" means that filter is not applied.
- The "Check existing reports first" panel on the report form uses exactly the same rules (`search_reports()` in `app/reports.py`).

**Status (CF-13, CF-11)**
- Staff can switch between Submitted, In Progress and Resolved, including moving a resolved report back to In Progress
  (Product Owner decision: a fixed problem can break again).
- Resolving requires a non-empty resolution note.
- The resolution note is shown to students only while the report is Resolved.

## Tests

```bash
pytest -v
```

68 automated tests. Test IDs match the team's test record in Confluence (TC-01 to TC-55).

| File | Story | Test IDs |
|---|---|---|
| `tests/test_required_cases.py` | Required coverage from the assignment | TC-01 to TC-10 |
| `tests/test_cf7_report_list.py` | CF-7 report list | TC-11 to TC-14 |
| `tests/test_cf5_choices.py` | CF-5 fixed locations and categories | TC-15 to TC-19 |
| `tests/test_cf8_report_detail.py` | CF-8 report details and not found page | TC-20 to TC-24 |
| `tests/test_cf12_auth.py` | CF-12 sign-in and roles | TC-25 to TC-29 |
| `tests/test_cf13_staff_update.py` | CF-13 staff status update | TC-30 to TC-34 |
| `tests/test_cf9_search.py` | CF-9 keyword search | TC-35 to TC-38 |
| `tests/test_cf21_access_denied.py` | CF-21 access-denied page | TC-39 to TC-42 |
| `tests/test_cf11_resolution_note.py` | CF-11 resolution note on details | TC-43 to TC-46 |
| `tests/test_cf6_check_similar.py` | CF-6 check before submitting | TC-47 to TC-50 |
| `tests/test_cf10_location_filter.py` | CF-10 location filter | TC-51 to TC-55 |
| `tests/test_smoke.py` | App starts, pages load, demo accounts exist | — |

Tests use a temporary database, so they never touch `instance/campusfix.sqlite`.

## Project structure

```
app/
  __init__.py      app factory, blueprints, 403 access-denied page   (CF-21)
  constants.py     locations, categories, statuses, roles
  schema.sql       database tables
  db.py            SQLite connection, init-db command, demo accounts
  auth.py          login / logout / role checks                      (CF-12)
  reports.py       submit, check, list, search, detail               (CF-4 to CF-11, CF-6)
  staff.py         staff dashboard and status update                 (CF-13)
  templates/       HTML pages (Jinja)
  static/          CSS
tests/             pytest tests (see table above)
```

## Team

| Member | Role | Stories |
|---|---|---|
| 蕭博宇 | Scrum Master, Developer | CF-7, CF-21, CF-6 |
| 劉佑平 | Product Owner, Developer | CF-12, CF-9 |
| chenhao | Developer | CF-8, CF-13 |
| Elvis | Developer | CF-4, CF-10 |
| 李科漢 | Developer | CF-5, CF-11 |

Two one-week sprints: Sprint 1 (11/11) 21/21 points, Sprint 2 (11/18) 17/17 points.

## Team workflow

1. Claim a story in Jira and move it to **進行中** (In Progress).
2. Get the latest `main` and create a branch named after the Jira key:
   ```bash
   git checkout main
   git pull
   git checkout -b CF-4-submit-report
   ```
3. If your story depends on another story, start only after that story is merged into `main`.
4. Implement the story and its tests; run `pytest -v` before pushing.
5. Commit with the Jira key at the start of the message, for example `CF-4 Add report validation`, then push the branch.
6. Open a Pull Request titled with the Jira key, move the Jira card to **送審** (In Review) and ask another member to review.
7. After the review is approved, merge into `main`, add the merge commit or PR link to the Jira story and move it and its
   subtasks to **完成** (Done) when it meets the Definition of Done.

Never commit directly to `main`, and never commit `.venv/` or `instance/`.

## Acknowledgements

AI assistance (Claude and other AI coding assistants) was used to generate the initial project skeleton and to help team
members write code, tests, reviews and documentation. Every change was reviewed by another team member and every team
member can explain the code they submitted.
