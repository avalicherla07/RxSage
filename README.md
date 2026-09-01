# RxSage

Clinical decision support API for US dental professionals. Given a patient's medications, conditions, allergies, and a candidate dental drug, RxSage returns structured, dentist-workflow-ordered guidance across three tiers — an immediate headline, standard workflow sections (anesthetic, antibiotic, analgesic, sedation safety), and full clinical explanation with sourced evidence.

---

## How it works

1. **Evidence gathering** — drug interaction data is pulled from a curated local DB, OpenFDA, DailyMed, PubMed, KEGG, and MedlinePlus concurrently.
2. **Evidence ranking** — all sources are scored by trust tier, conflict-detected, and packaged with quality metadata.
3. **AI reasoning** — GPT-4o synthesizes the evidence with full patient context (age, sex, conditions, allergies) to produce a structured clinical response.
4. **Two-layer caching** — drug-pair data is cached in memory (30-minute TTL) so repeated lookups for the same drugs don't re-hit external APIs. Full responses are cached in Supabase keyed by exact request hash.

---

## Response structure

Every response returns three tiers. The calling system controls what to display.

| Tier | Fields | Purpose |
|------|--------|---------|
| **Tier 1 — Immediate** | `headline`, `proceed`, `risk_level`, `flags` | Dentist sees without any interaction |
| **Tier 2 — Standard** | `summary`, `key_interactions`, `anesthetic_safety`, `antibiotic_safety`, `analgesic_safety`, `sedation_safety`, `oral_manifestations`, `procedure_context` | One tap to expand |
| **Tier 3 — Deep** | `clinical_explanation`, `patient_risk_factors`, `sources`, `evidence_quality`, `monitoring_recommendations` | Full clinical detail |

`proceed` is always one of: `safe` · `caution` · `modify` · `do_not_proceed`

---

## API

### Authentication

All endpoints require an `X-API-Key` header.

```
X-API-Key: your-api-key
```

### Rate limits

| Window | Limit |
|--------|-------|
| Per minute | 10 requests |
| Per hour | 100 requests |
| Per day | 500 requests |

### Endpoints

#### `POST /v1/analyze`

Analyze a candidate medication for a specific patient.

**Request**

```json
{
  "patient": {
    "age": 68,
    "sex": "male",
    "conditions": ["atrial fibrillation", "heart failure"],
    "allergies": ["penicillin"]
  },
  "current_medications": [
    {"name": "Warfarin", "dosage": "5mg"},
    {"name": "Carvedilol", "dosage": "25mg"}
  ],
  "candidate_medication": {
    "name": "Clarithromycin",
    "dosage": "500mg"
  }
}
```

**Response (excerpt)**

```json
{
  "headline": "Clarithromycin may significantly raise warfarin levels — review INR before extraction.",
  "proceed": "do_not_proceed",
  "risk_level": "high",
  "summary": "Clarithromycin inhibits CYP3A4, which may increase warfarin levels and elevate INR...",
  "anesthetic_safety": {
    "recommended_agent": "Lidocaine 2% with epinephrine 1:100,000",
    "epinephrine_status": "limit",
    "epinephrine_guidance": "Limit to 2 cartridges given carvedilol (non-selective beta-blocker)."
  },
  "antibiotic_safety": {
    "candidate_antibiotic_status": "avoid — CYP3A4 inhibition raises warfarin levels significantly",
    "safe_alternatives": [
      {"name": "Clindamycin", "dosage": "300mg TID x 5-7 days", "reason": "No CYP interaction with warfarin."}
    ]
  },
  "confidence": "high",
  "fallback": false
}
```

Full request/response examples are in [docs/examples/](docs/examples/).

#### `GET /health`

Returns service health status.

#### `POST /v1/keys` · `DELETE /v1/keys/{id}`

API key provisioning and revocation. Requires the `ADMIN_KEY` header.

---

## Setup

### Requirements

- Python 3.11+
- [Supabase](https://supabase.com) project
- OpenAI API key (GPT-4o)

### Local development

```bash
# 1. Clone and install
git clone https://github.com/your-org/rxsage.git
cd rxsage
pip install .

# 2. Configure environment
cp .env.example .env
# Fill in OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, ADMIN_KEY

# 3. Apply database migrations
supabase db push

# 4. Start the server
uvicorn main:app --reload --port 8000
```

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key (GPT-4o) |
| `SUPABASE_URL` | Yes | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | — | Supabase service role key |
| `ADMIN_KEY` | Yes | — | Key used to authenticate key management endpoints |
| `PORT` | No | `8000` | Port the server binds to |
| `PUBMED_ENABLED` | No | `true` | Toggle PubMed evidence retrieval |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG` · `INFO` · `WARNING` · `ERROR`) |
| `RATE_LIMIT_PER_MINUTE` | No | `10` | Requests per minute per key |
| `RATE_LIMIT_PER_HOUR` | No | `100` | Requests per hour per key |
| `RATE_LIMIT_PER_DAY` | No | `500` | Requests per day per key |

### Docker

```bash
docker build -t rxsage .
docker run -p 8000:8000 --env-file .env rxsage
```

---

## Project structure

```
rxsage/
├── main.py                  # FastAPI app, exception handlers, router wiring
├── core/
│   └── config.py            # Pydantic settings (reads .env)
├── api/
│   ├── middleware/
│   │   ├── auth.py          # X-API-Key validation
│   │   └── rate_limiter.py  # Per-key rate limiting
│   └── routes/
│       ├── analyze.py       # POST /v1/analyze
│       ├── health.py        # GET /health
│       └── keys.py          # Key provisioning
├── services/
│   ├── orchestrator.py      # Pipeline coordinator — caching, gathering, reasoning
│   ├── openai_client.py     # GPT-4o structured output
│   ├── interaction_db.py    # Local curated drug interaction DB
│   ├── openfda.py           # OpenFDA drug label warnings
│   ├── dailymed.py          # DailyMed interaction sections
│   ├── pubmed.py            # PubMed clinical evidence
│   ├── kegg_client.py       # KEGG drug interactions
│   ├── medlineplus.py       # MedlinePlus drug info
│   ├── evidence_ranker.py   # Trust scoring, conflict detection, quality summary
│   └── drug_normaliser.py   # Drug name normalization
├── models/
│   ├── request.py           # AnalysisRequest, PatientInput, MedicationInput
│   └── response.py          # AnalysisResponse and all sub-models
├── db/
│   ├── supabase.py          # Response cache and audit log
│   └── drug_knowledge.py    # Drug knowledge queries
├── supabase/
│   └── migrations/          # SQL migrations (schema + seed data)
├── docs/
│   └── examples/            # Sample request and response JSON
└── tests/
    ├── test_analyze.py      # Request/response model + e2e tests
    ├── test_interaction_db.py
    ├── test_evidence_ranker.py
    ├── test_drug_normaliser.py
    └── test_config.py
```

---

## Testing

```bash
pip install pytest pytest-asyncio hypothesis
pytest
```

Tests use [Hypothesis](https://hypothesis.readthedocs.io/) for property-based validation of request and response schemas, and `pytest-asyncio` for the end-to-end route test.

---

## Evidence sources

| Source | Type | Used for |
|--------|------|---------|
| Local DB | Curated interaction database | Primary interaction lookup — instant, no network |
| OpenFDA | FDA drug labels | Official warnings and contraindications |
| DailyMed | NLM drug labeling | Interaction sections from approved labels |
| PubMed | Clinical literature | Supporting evidence, mechanism studies |
| KEGG | Drug–drug interaction DB | Pharmacokinetic interaction data |
| MedlinePlus | NLM consumer drug info | Supplementary drug information |

Evidence is trust-scored and conflict-detected before being passed to GPT-4o. The response always includes an `evidence_quality` block describing sources consulted, conflicts found, and overall quality rating (`strong` · `moderate` · `limited`).
