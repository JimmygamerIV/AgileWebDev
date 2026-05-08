# AgileWebDev project

|  UWA ID  | Name                         | GitHub Username |
|----------|------------------------------|-----------------|
| 24011123 | James Caporn                 | JimmygamerIV    |
| 24048538 | Pengyang Yin                 | WishingU        |
| 24331036 | Johar Khan                   | joharalam03     |
| 24405084 | Kai Latiola                  | klatiolais1     |


The creation of the web application should be done in a private GitHub repository that includes a README containing:
a description of the purpose of the application, explaining its design and use.
a table with with each row containing the i) UWA ID ii) name and iii) Github user name of the group members.
instructions for how to launch the application.
instructions for how to run the tests for the application.

### First-time setup

Clone the repo, then create a virtual environment and install dependencies.

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


## Database

The app uses Alembic for database migrations. Migrations apply automatically on startup — just run:

    python app.py

If you change `models.py`, generate a migration:

    alembic revision --autogenerate -m "describe the change"

Commit both `models.py` and the new file in `alembic/versions/`.