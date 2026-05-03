# POSTNOW — Automated AI Marketing Assistant

AI-powered promotional poster + bilingual caption generator for Cambodian coffee shops.

---

## Project Structure

```
postnow/
├── backend/
│   ├── main.py              ← FastAPI app entry point
│   ├── db.py                ← SQLite database setup
│   ├── requirements.txt
│   ├── .env.example         ← Copy this to .env and fill in your keys
│   ├── routes/
│   │   ├── auth.py          ← Register, Login, /me
│   │   ├── profile.py       ← Brand profile save/get
│   │   └── generate.py      ← Orchestrates both AI agents
│   └── agents/
│       ├── caption_agent.py ← Claude (Anthropic) bilingual caption generation
│       └── image_agent.py   ← Gemini (Nanobana) poster generation
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.js
        ├── App.vue
        ├── api.js           ← Axios with auth token injection
        ├── router/index.js
        ├── stores/auth.js   ← Pinia auth store
        └── views/
            ├── LoginView.vue
            ├── OnboardingView.vue
            ├── HomeView.vue
            ├── ResultView.vue
            └── HistoryView.vue
```

---

## Setup (Step by Step)

### 1. Backend

```bash
cd postnow/backend

# Copy and fill in your API keys
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY and GEMINI_API_KEY

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 8000
```

The API will be live at: http://localhost:8000
Interactive API docs: http://localhost:8000/docs

---

### 2. Frontend

```bash
cd postnow/frontend

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

The app will be live at: http://localhost:5173

---

## API Keys You Need

| Key | Where to get it |
|-----|----------------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com → API Keys |
| `GEMINI_API_KEY` | https://aistudio.google.com → Get API Key |

---

## How It Works

1. User registers and logs in
2. Onboarding collects: Shop Name, Aesthetic (Cozy/Bold/Minimalist), Brand Colors
3. User enters a promotion prompt (e.g. "Buy 1 Get 1 Latte this weekend")
4. Backend calls **caption_agent** (Claude) and **image_agent** (Gemini) IN PARALLEL
5. Claude generates: English caption + Khmer caption + 5 hashtags
6. Gemini generates: Branded promotional poster image
7. Result screen shows everything — user can edit, download, or Renovate

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, get JWT token |
| GET | `/auth/me` | Get current user + profile status |
| POST | `/profile` | Save brand profile |
| GET | `/profile` | Get brand profile |
| POST | `/generate` | Generate poster + captions |
| GET | `/generate/history` | Last 20 generations |
