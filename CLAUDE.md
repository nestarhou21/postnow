# POSTNOW — CLAUDE.md
> Read this entire file before touching any code.
> This is the single source of truth for the POSTNOW project.

---

## What is POSTNOW?

POSTNOW is an AI-powered marketing content generation system built for
local coffee shop owners in Cambodia. It lets a non-technical owner enter
a plain-language promotion prompt (e.g. "Buy 1 Get 1 Latte this weekend")
and receive within under 2 minutes:

- A branded promotional **poster image** (via Gemini/Nanobana API)
- A **bilingual caption** in English + Khmer (via Claude API + fine-tuned mBART model)
- **5 hashtags** mixing English and Khmer

The system personalises every output using a **brand profile** collected
during onboarding: Shop Name, Aesthetic (Cozy / Bold / Minimalist), and
Brand Color Palette.

**Internship context:** This is Hou Nestar's 4th-year CADT internship project
at CAMBO NEXTGEN INNOVATIVE TECHNOLOGIES CO., LTD., supervised by Lim Nithie,
advised by Mr. Heng Soklay. Defense date: May 27, 2026.

---

## Tech Stack

### Backend (Python)
- **FastAPI** — REST API framework
- **SQLite** — lightweight DB via `db.py` (file: `postnow.db`)
- **Anthropic Claude API** — `claude-sonnet-4-6` for caption generation (fallback)
- **Google Gemini API** — `gemini-2.0-flash-preview-image-generation` for posters
- **mBART-large-50** — fine-tuned in-house model for bilingual caption generation (primary)
- **JWT auth** — `python-jose`, tokens stored client-side
- **passlib[bcrypt]** — password hashing

### Frontend (Vue.js)
- **Vue.js 3** — Composition API
- **Vite** — dev server on port 5173, proxies `/api/*` → `localhost:8000`
- **Pinia** — auth store
- **Vue Router 4** — client-side routing
- **Axios** — HTTP client with auth interceptor in `src/api.js`

### ML / Fine-tuning
- **Model:** `facebook/mbart-large-50` (primary caption generator)
- **Fallback:** Claude API (`caption_agent.py`) when model confidence is low
- **Training data:** synthetically generated via Claude, stored in `ml/data/`
- **Framework:** HuggingFace Transformers + datasets
- **Training script:** `ml/train.py`
- **Inference:** `ml/infer.py` — loaded at backend startup

---

## Project Structure

```
postnow/
├── CLAUDE.md                  ← YOU ARE HERE
├── README.md
├── backend/
│   ├── main.py                ← FastAPI app entry, mounts all routers
│   ├── db.py                  ← SQLite init + get_db() context manager
│   ├── requirements.txt
│   ├── .env                   ← NOT committed — copy from .env.example
│   ├── .env.example
│   ├── routes/
│   │   ├── auth.py            ← POST /auth/register, /auth/login, GET /auth/me
│   │   ├── profile.py         ← POST/GET /profile (brand profile)
│   │   └── generate.py        ← POST /generate (orchestrates both agents)
│   └── agents/
│       ├── caption_agent.py   ← Claude API fallback caption generator
│       └── image_agent.py     ← Gemini poster generator
├── ml/
│   ├── data/
│   │   ├── raw/               ← Raw synthetic data JSONLines files
│   │   └── processed/         ← Tokenised + split datasets
│   ├── generate_data.py       ← Uses Claude API to generate training pairs
│   ├── train.py               ← Fine-tunes mBART-large-50
│   ├── infer.py               ← Inference wrapper (loaded by backend)
│   ├── evaluate.py            ← BLEU + manual eval
│   └── model/                 ← Saved fine-tuned model weights (gitignored)
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.js
        ├── App.vue
        ├── api.js             ← Axios instance, injects Bearer token automatically
        ├── router/
        │   └── index.js       ← Routes + auth guards + onboarding redirect
        ├── stores/
        │   └── auth.js        ← Pinia: login, register, fetchMe, logout
        └── views/
            ├── LoginView.vue       ← Register + Login (tabbed)
            ├── OnboardingView.vue  ← 3-step: shop name → aesthetic → colors
            ├── HomeView.vue        ← Generator: prompt input + template picker
            ├── ResultView.vue      ← Poster + captions + Accept/Renovate/Download
            └── HistoryView.vue     ← Last 20 generations
```

---

## How to Run

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Then fill in API keys
uvicorn main:app --reload --port 8000
```

API live at: http://localhost:8000
Swagger docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```

App live at: http://localhost:5173

### ML Training (Google Colab recommended)
```bash
cd ml
pip install transformers datasets sentencepiece torch sacrebleu
python generate_data.py      # Step 1: generate synthetic training data
python train.py              # Step 2: fine-tune mBART
python evaluate.py           # Step 3: evaluate BLEU score
```

---

## Environment Variables (.env)

```
ANTHROPIC_API_KEY=...         # console.anthropic.com
GEMINI_API_KEY=...            # aistudio.google.com
SECRET_KEY=...                # random 32-char string for JWT signing
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=postnow.db
USE_LOCAL_MODEL=true          # set false to always use Claude fallback
LOCAL_MODEL_PATH=ml/model     # path to saved fine-tuned mBART weights
```

---

## Database Schema

### `users`
| column | type | notes |
|--------|------|-------|
| id | INTEGER PK | auto |
| email | TEXT UNIQUE | |
| password | TEXT | bcrypt hashed |
| created_at | TEXT | datetime |

### `brand_profiles`
| column | type | notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | INTEGER FK | one per user |
| shop_name | TEXT | e.g. "Slow Drip Café" |
| aesthetic | TEXT | Cozy / Bold / Minimalist |
| colors | TEXT | JSON array e.g. ["#C8A27C","#5A3E2B"] |
| updated_at | TEXT | |

### `generations`
| column | type | notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | INTEGER FK | |
| prompt | TEXT | user's raw promotion prompt |
| template_id | TEXT | centered / text_banner / lifestyle / minimal |
| en_caption | TEXT | |
| kh_caption | TEXT | |
| hashtags | TEXT | |
| image_url | TEXT | base64 data URL (truncated for storage) |
| created_at | TEXT | |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Create account → returns JWT |
| POST | `/auth/login` | No | Login → returns JWT |
| GET | `/auth/me` | Yes | Current user + has_profile flag |
| POST | `/profile` | Yes | Save/update brand profile |
| GET | `/profile` | Yes | Get brand profile |
| POST | `/generate` | Yes | Generate poster + captions |
| GET | `/generate/history` | Yes | Last 20 generations |

### POST `/generate` request body
```json
{
  "prompt": "Buy 1 Get 1 Latte this weekend",
  "template_id": "centered"
}
```

### POST `/generate` response
```json
{
  "generation_id": 1,
  "en_caption": "...",
  "kh_caption": "...",
  "hashtags": "#CoffeeTime #SlowDrip ...",
  "image_data_url": "data:image/png;base64,...",
  "prompt_used": "..."
}
```

---

## Caption Generation Architecture (Two-Layer)

### Layer 1 — Fine-tuned mBART model (PRIMARY)
- Model: `facebook/mbart-large-50` fine-tuned on synthetic coffee shop data
- Input: `"{shop_name} | {aesthetic} | {colors} | {promotion_prompt}"`
- Output: `"[EN] ... [KH] ... [TAGS] ..."`
- Loaded once at backend startup via `ml/infer.py`
- Fast (< 3 seconds on CPU)

### Layer 2 — Claude API fallback (SECONDARY)
- Used when: `USE_LOCAL_MODEL=false` OR local model confidence < threshold
- File: `backend/agents/caption_agent.py`
- Model: `claude-sonnet-4-6`
- Same structured output format: `[EN] / [KH] / [TAGS]`

### How generate.py decides which to use
```python
if USE_LOCAL_MODEL and model_loaded:
    result = infer.generate_caption(...)   # mBART
else:
    result = caption_agent.generate_caption(...)  # Claude fallback
```

---

## Image Generation

- File: `backend/agents/image_agent.py`
- API: Google Gemini `gemini-2.0-flash-preview-image-generation`
- Returns: base64-encoded PNG as data URL
- Template styles: `centered`, `text_banner`, `lifestyle`, `minimal`
- Aesthetic moods: Cozy (warm soft), Bold (high contrast), Minimalist (clean neutral)

---

## Brand Guidelines (from official POSTNOW brand doc)

### Colors
| Name | Hex | Usage |
|------|-----|-------|
| Soft Latte | `#C8A27C` | Primary, poster backgrounds |
| Cocoa Brown | `#5A3E2B` | Depth, secondary text |
| Muted Sage | `#7FA39C` | Accent for calm promotions |
| Slate Gray | `#3A3A3A` | Body text |
| Caramel Gold | `#C8A97E` | Supporting |
| Soft Lavender | `#E9ECF5` | Supporting |

### Typography
| Font | Role |
|------|------|
| DM Sans | Body font (English) |
| Helvetica World | Header font (English) |
| Battambang | Khmer content font |

### Aesthetics
- **Cozy** — warm, soft lighting, inviting, terracotta tones
- **Bold** — vibrant, high contrast, energetic, emojis allowed
- **Minimalist** — clean, lots of white space, neutral palette, no emojis

### Logo concept
Coffee cart house icon with coffee beans on roof, open door/window
symbolising social media opportunity and community.

---

## ML Training Data Format

Each training example in `ml/data/raw/` is a JSONL record:
```json
{
  "input": "Slow Drip Café | Cozy | #C8A27C,#5A3E2B | Buy 1 Get 1 Latte this weekend",
  "output": "[EN]\nStart your weekend right with a Buy 1 Get 1 Latte deal at Slow Drip Café. Warm brews, cozy vibes — bring a friend and enjoy the perfect sip together. This weekend only!\n\n[KH]\nចំណាយតែ១ ទទួលបាន២! មកជួបគ្នានៅ Slow Drip Café ហើយរីករាយជាមួយកាហ្វេឡាតេ ២កែវ ក្នុងតម្លៃ១. ឱកាសនេះមានត្រឹមតែចុងសប្តាហ៍ប៉ុណ្ណោះ!\n\n[TAGS]\n#SlowDripCafe #BuyOneGetOne #PhnomPenhCoffee #កាហ្វេភ្នំពេញ #WeekendVibes"
}
```

---

## Coding Conventions

- **Never hardcode API keys** — always `os.getenv()`
- **All backend routes use Pydantic models** for request + response
- **Never use `\n` in Vue templates** — use separate elements
- **All async DB-heavy work** runs in `ThreadPoolExecutor` via `run_in_executor`
- **sessionStorage** used to pass generate result to ResultView (not Pinia — keeps it simple)
- **Error handling:** all API calls wrapped in try/catch, user-facing errors shown in template
- **No TypeScript** — plain JS for frontend (keep it simple for internship scope)
- **Python files:** snake_case. Vue files: PascalCase components, camelCase variables

---

## Common Tasks

### Add a new API route
1. Create function in relevant `routes/` file
2. Add `@router.get/post(...)` decorator with Pydantic model
3. No need to touch `main.py` — routers are already mounted

### Modify the caption prompt
→ Edit `SYSTEM_PROMPT_TEMPLATE` in `backend/agents/caption_agent.py`

### Change image generation style
→ Edit `TEMPLATE_STYLES` or `AESTHETIC_MOODS` dicts in `backend/agents/image_agent.py`

### Add a new Vue screen
1. Create `src/views/NewView.vue`
2. Add route in `src/router/index.js`
3. Link from existing screen using `router.push('/new-path')`

### Regenerate training data
```bash
cd ml
python generate_data.py --count 500 --output data/raw/batch2.jsonl
```

### Re-run fine-tuning
```bash
cd ml
python train.py --epochs 5 --batch_size 8 --output model/
```

---

## What Is NOT Built Yet (TODO)

- [ ] `ml/generate_data.py` — synthetic training data generator
- [ ] `ml/train.py` — mBART fine-tuning script
- [ ] `ml/infer.py` — inference wrapper loaded by backend
- [ ] `ml/evaluate.py` — BLEU score evaluation
- [ ] Backend integration of local model in `generate.py`
- [ ] Khmer font (Battambang) loaded in frontend
- [ ] Generation history images (currently only text saved to DB)
- [ ] Mobile layout polish for ResultView

---

## Do NOT

- Do NOT change the DB schema without updating `db.py` init_db()
- Do NOT expose API keys in frontend code ever
- Do NOT use `WidthType.PERCENTAGE` in any docx work
- Do NOT add TypeScript — keep plain JS
- Do NOT rename the `[EN]`, `[KH]`, `[TAGS]` section markers — the parser depends on them
- Do NOT switch from `claude-sonnet-4-6` to another model without testing output format
