# UWA Social Timetable

A web app that helps UWA students see where their friends are on campus throughout the day. Students upload their class timetable (ICS file or URL), and the app plots their classes on a map, shows who else is in the same room, and lists which friends are currently in class.

## Team

|  UWA ID  | Name                         | GitHub Username |
|----------|------------------------------|-----------------|
| 24011123 | James Caporn                 | JimmygamerIV    |
| 24048538 | Pengyang Yin                 | WishingU        |
| 24331036 | Johar Khan                   | joharalam03     |
| 24405084 | Kai Latiolais                | klatiolais1     |

## Features

- **Authentication** — sign up with a UWA email, sign in/out, change password, change nickname, upload custom avatar.
- **Timetable import** — upload a `.ics` file or paste an ICS URL; classes are auto-mapped to building/room locations on campus.
- **Interactive map** — Leaflet map showing today's classes, route between them, and class details on click.
- **Friends** — search users, send/accept/reject/cancel friend requests, favourite friends, remove friends.
- **Friends on campus** — live sidebar of friends currently in class.
- **Friend profiles** — read-only view of any user's profile, with mutual friend count and their current class.

## Tech stack

- **Backend**: Python, Flask, SQLAlchemy, SQLite, Flask-WTF, Flask-Login
- **Frontend**: Jinja2 templates, Bootstrap 5, Leaflet, vanilla JS (AJAX)
- **Migrations**: Alembic
- **Testing**: pytest, Selenium

## Getting Started

### Prerequisites

- Python **3.12 or 3.13** (Python 3.14 is not supported — SQLAlchemy breaks on it)
- Git

### First-time setup

**macOS / Linux:**

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (Command Prompt):**

```cmd
py -3.12 -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Running the app

After activating the virtual environment:

```bash
python app.py
```

The app runs at <http://127.0.0.1:5000>.

To exit the virtual environment when done: `deactivate`.

### Seeding test data (optional)

To populate the database with test users (`john`, `bombo`, `steve` — all with password `test1234`) plus a few pending friend requests to your account, first sign up through the app, then run:

```bash
python seed.py 
```

## Running the tests

Make sure dev dependencies are installed:

```bash
pip install -r test-requirements.txt
```

Run the unit tests:

```bash
pytest test/
```

Run the Selenium end-to-end tests (requires Chrome installed):

```bash
pytest test/test_integration.py
```

## Database migrations

The app uses Alembic for schema versioning. After pulling schema changes:

```bash
alembic upgrade head
```

To generate a new migration after editing `models.py`:

```bash
alembic revision --autogenerate -m "describe the change"
```

Commit both the model change and the generated migration file in `alembic/versions/`.

## Project structure

```
app.py               Main Flask app + index/event/profile routes
auth.py              Auth blueprint (signup/signin/logout/password reset)
friends.py           Friends blueprint (requests, search, profiles, on-campus)
models.py            SQLAlchemy ORM models
forms.py             Flask-WTF form definitions
database.py          DB engine + session factory
config.py            Configuration loaded from .env
templates/           Jinja2 HTML templates
static/              CSS, JavaScript, images
test/                pytest unit + integration tests
alembic/             Database migration scripts
```

## License

Educational project for CITS3403 Agile Web Development at UWA.