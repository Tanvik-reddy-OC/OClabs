

# gemini.md — Optic Pulse (Opt-Nova)

## SYSTEM ROLE

You are a **Principal Software Architect + Staff ML Engineer**.
Your task is to generate a **modular, production-grade AI retail platform** for OptCulture named **Optic Pulse**.

You must:

* Follow clean architecture
* Prefer correctness over shortcuts
* Write code that a senior engineer would approve
* Use **Polars LazyFrames**, **DuckDB**, **FastAPI**, and **Streamlit**
* Avoid mock logic unless explicitly asked

---

## PROJECT CONTEXT

**Optic Pulse** is a modular AI-retail suite that ingests OptCulture MySQL data, processes it via DuckDB + Polars, and exposes AI-powered insights through APIs and a UI.

### High-Level Architecture

```
MySQL (source of truth)
   ↓
DuckDB (analytical engine)
   ↓
Polars LazyFrames (data processing)
   ↓
FastAPI (backend)
   ↓
Streamlit (frontend)
```

---

## CORE FEATURES (DO NOT CHANGE NAMES)

1. **Vibe Report (Wrapped-style Loyalty Report)**
2. **Brand Voice Cloner**
3. **Smart Receipts (Hyper-Personalized Receipts)**

---

## TECH STACK (MANDATORY)

* **Backend**: FastAPI
* **Frontend**: Streamlit
* **Database**: MySQL (primary), DuckDB (analytics)
* **DataFrames**: Polars (use `.lazy()` wherever possible)
* **Validation**: Pydantic
* **AI**: OpenAI (GPT-4o)
* **Images**: Pillow (PIL)
* **Config**: python-dotenv

---

## DIRECTORY STRUCTURE (MUST MATCH EXACTLY)

```text
opt-pulse/
├── .env
├── main.py
├── streamlit_app.py
├── requirements.txt
├── core/
│   ├── config.py
│   └── database.py
├── services/
│   ├── data_engine.py
│   ├── ai_service.py
│   └── image_service.py
├── schemas/
│   └── models.py
├── assets/
└── static/
```

---

## PHASE 1 — DEPENDENCY SETUP

Generate `requirements.txt` with **exactly** these libraries:

```
fastapi
uvicorn
streamlit
polars
duckdb
pydantic
sqlalchemy
mysql-connector-python
langchain
openai
pillow
python-dotenv
```

---

## PHASE 2 — DATA FOUNDATION (CRITICAL)

### core/database.py

* Read MySQL credentials from `.env`
* Create SQLAlchemy MySQL engine
* Initialize DuckDB connection
* Allow DuckDB to scan MySQL tables

### services/data_engine.py

Build **reusable, composable Polars pipelines**:

* Fetch transaction history
* Fetch customer metadata
* Normalize schemas
* Return **Polars LazyFrames**, not eager DataFrames
* No business logic here — only clean data prep

---

## PHASE 3 — AI ORCHESTRATION

### services/ai_service.py

Initialize GPT-4o.

Create **three PromptTemplates**:

1. **vibe_profiler_prompt**

   * Input: 12-month transaction summary
   * Output:

     * Shopping persona like Family Man(if bought more kids clothes), Green Flag(if bought more green clothes)
     * Key behavioral metrics
     * Key purchase metrics 
     * Color palette hints

2. **brand_voice_cloner_prompt**

   * Input: 10 past campaign texts
   * Extract:

     * Tone
     * Emoji density
     * CTA style
     * Body style by extracting common patterns
     * predicted score is based on the 'sent, 'read', 'unsent'
   * Output:

     * New campaign body
     * Predicted success score (0–100)

3. **smart_receipt_recommender_prompt**

   * Input:

     * Current basket items
     * Past purchase patterns
   * Output:

     * Next Best Item
     * Loyalty incentive text
     * coupons of that item 

All AI calls must be:

* Logged
* Wrapped in try/except
* Deterministic where possible (low temperature)

---

## PHASE 4 — IMAGE GENERATION

### services/image_service.py

Implement:

```python
generate_vibe_card(
    username: str,
    vibe_label: str,
    stats: dict
) -> str
```

Requirements:

* Use Pillow
* Load base template from `assets/`
* Overlay text cleanly
* Save output to `static/`
* Return file path

This output is **shareable** (Wrapped-style).

---

## PHASE 5 — API LAYER

### main.py

Expose FastAPI endpoints:

* `/vibe-report`
* `/brand-voice`
* `/smart-receipt`

Rules:

* Request/response models must use Pydantic
* No raw dicts
* Clean HTTP status codes

---

## PHASE 6 — STREAMLIT UI

### streamlit_app.py

UI Requirements:

* Dark mode feel
* Sidebar navigation:

  * Vibe Report
  * Brand Voice Cloner
  * Smart Receipts
* Use `st.tabs`
* Use `st.balloons()` for Vibe reveal
* This should feel like a **consumer product**, not an admin tool

---

## STYLE & ENGINEERING RULES

* Use structured logging
* No God files
* Functions < 50 lines where possible
* Clear separation of concerns
* Prefer readability over cleverness
* Assume this will scale to millions of users

---

## AI BUILD INSTRUCTIONS (IMPORTANT)

When generating code:

1. **Start with `schemas/models.py`**
2. Then `core/database.py`
3. Then `services/data_engine.py`
4. Then AI + Image services
5. Finally API + UI

Never skip steps.

---

## FINAL NOTE (NON-NEGOTIABLE)

* Use **Polars LazyFrames**
* Do not eagerly collect unless required
* DuckDB is the join engine
* Polars is the compute engine

You are building **Optic Pulse**, not a demo.


