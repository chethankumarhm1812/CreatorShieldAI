# CreatorShield AI Backend

FastAPI + SQLAlchemy + SQLite demo backend for the Guidewire-inspired insurance core.

## Run

Python 3.12 recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

Demo users:
- creator@example.com / Creator@123
- adjuster@example.com / Adjuster@123

The simulator intentionally separates PolicyCenter, ClaimCenter and BillingCenter responsibilities but does not claim to be licensed Guidewire software.
