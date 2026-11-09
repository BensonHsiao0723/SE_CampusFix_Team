# CampusFix

A small web application for students to report campus problems and for staff to track their resolution.
Built with Python, Flask and SQLite for the NTPU Software Engineering course.

> Status: **project skeleton**. Pages and routes exist; feature logic is marked `TODO CF-xx`
> (Jira story keys) and is implemented by the team during the sprints.

## Requirements

- Python 3.10 or newer (tested with 3.14)
- Windows: use `py`; macOS/Linux: use `python3`

## Setup (first time)

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask --app app init-db
```

macOS/Linux: `python3 -m venv .venv` and `source .venv/bin/activate`.

`init-db` creates `instance/campusfix.sqlite` and the demo accounts.
**It deletes all existing data**, so run it only once (or when you want a clean demo).

## Run

```bash
flask --app app run --debug
```

Open http://127.0.0.1:5000

Data is stored in `instance/campusfix.sqlite`, so it survives page refreshes and application restarts.

## Demo accounts

Fictional accounts for demonstration only:

| Role    | Username   | Password     |
|---------|------------|--------------|
| Student | `student1` | `student123` |
| Staff   | `staff1`   | `staff123`   |

## Tests

```bash
pytest -v
```

- `tests/test_smoke.py`: checks that the skeleton starts and the pages load.
- `tests/test_required_cases.py`: the 10 required test cases (TC-01 to TC-10), currently skipped.
  Remove the `skip` mark when you implement the related story.

## Project structure

```
app/
  __init__.py      app factory, registers blueprints
  constants.py     locations, categories, statuses, roles
  schema.sql       database tables
  db.py            SQLite connection, init-db command, demo accounts
  auth.py          login / logout / role checks            (CF-12)
  reports.py       submit, list, detail, search            (CF-4 to CF-11)
  staff.py         staff dashboard and status update       (CF-13)
  templates/       HTML pages (Jinja)
  static/          CSS
tests/             pytest tests
```

## Search behaviour (Sprint 2)

- The keyword matches the title **or** the description, ignoring letter case and leading/trailing spaces.
- When a keyword and a location are both given, a report must match **both** (AND).
- An empty keyword or "All locations" means that filter is not applied.

## Team workflow

1. Claim a story or task in Jira and move it to **進行中** (In Progress).
2. Get the latest `main` and create your own branch named after the Jira key:
   ```bash
   git checkout main
   git pull
   git checkout -b CF-4-submit-report
   ```
3. Implement the `TODO CF-xx` parts for your story and add or enable the related tests.
4. Run `pytest -v` before pushing.
5. Commit with the Jira key at the start of the message, for example `CF-4 Add report validation`, then push:
   ```bash
   git push -u origin CF-4-submit-report
   ```
6. Open a Pull Request titled with the Jira key, move the Jira card to **送審** (In Review) and ask another member to review.
7. After the review is approved, merge into `main`, add the PR link to the Jira story and move it to **完成** (Done) when it meets the Definition of Done.

Never commit directly to `main`, and never commit `.venv/` or `instance/`.

## Acknowledgements

The initial project skeleton was generated with AI assistance (Claude) and reviewed by the team.
