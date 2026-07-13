# Inkwell AI — Modern Python (FastAPI) & React Stack

This is the modernized, migrated version of Inkwell AI. It replaces the legacy PHP backend with a Python FastAPI server running on a local SQLite database, and replaces the HTML template with a clean React (Vite) Single-Page Application.

---

## Project Structure

```
inkwell-ai/
├── backend/                    ← Python FastAPI backend
│   ├── app/
│   │   ├── config.py           ← Environment variables & credentials
│   │   ├── database.py         ← SQLAlchemy & SQLite engine setup
│   │   ├── models.py           ← Database tables schemas (SQLite-safe)
│   │   ├── schemas.py          ← Pydantic validators
│   │   ├── security.py         ← JWT auth & passwords hashing
│   │   ├── routers/            ← FastAPI routers mapping REST endpoints
│   │   └── services/           ← Claude & GoCardless API clients
│   ├── db_init.py              ← DB table creator & user seeder
│   ├── main.py                 ← Backend entrypoint (CORS & Static files)
│   └── requirements.txt        ← Python packages requirements
└── frontend/                   ← React SPA (Vite)
    ├── src/
    │   ├── components/         ← UI blocks
    │   ├── context/            ← Auth state context & API wrappers
    │   ├── pages/              ← React pages (Home, Dashboard, Settings, etc.)
    │   ├── App.jsx             ← Routing controller
    │   ├── index.css           ← Premium layout & styles
    │   └── main.jsx            ← React renderer
    ├── index.html              ← HTML container
    └── package.json            ← Node dependencies
```

---

## 1. Backend Setup & Run

### 1a. Configure Environment Settings
Create a `.env` file inside `backend/` with the following variables:

```bash
# Environment
INKWELL_ENV=sandbox

# Anthropic Claude API Key
ANTHROPIC_API_KEY=sk-ant-your-key-here

# GoCardless Sandbox Keys (obtained from GC sandbox developer console)
GC_ACCESS_TOKEN=sandbox_your_gocardless_token
GC_WEBHOOK_SECRET=your_webhook_secret_here

# JWT Signature Secret (minimum 32 character hex string)
JWT_SECRET=super_secret_hex_signature_key_here
```

### 1b. Initialize SQLite Database
Make sure you are in the `backend/` directory, then run the database builder to scaffold tables and seed default accounts:

```bash
cd backend
python db_init.py
```

This creates the SQLite database file `inkwell.db` in `backend/` and seeds:
- **Admin**: `admin@inkwell.ai` (Password: `InkwellAdmin2024!`)
- **Test User**: `test@inkwell.ai` (Password: `password`)

### 1c. Start Uvicorn Dev Server
Launch the backend api server:

```bash
uvicorn main:app --reload --port 8000
```
- API will run at `http://localhost:8000`
- Swagger Documentation is auto-generated and visible at `http://localhost:8000/docs`

---

## 2. Frontend Setup & Run

Open a separate terminal window, navigate to the `frontend/` directory, install packages, and launch:

```bash
cd frontend
npm install
npm run dev
```

- React Dev server runs at `http://localhost:5173`
- Open your browser to `http://localhost:5173` and log in with your credentials!
