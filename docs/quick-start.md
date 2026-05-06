# RxSage Quick Start

Get your first API call working in under 10 minutes.

---

## Step 1 — Get your API key

Contact api@rxsage.com to request an API key. You'll receive a key that looks like `rsk_live_...`. Keep it secret — treat it like a password.

## Step 2 — Make your first call

```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "patient": {
      "age": 54,
      "sex": "female",
      "conditions": ["hypertension"],
      "allergies": []
    },
    "current_medications": [
      {"name": "Lisinopril", "dosage": "10mg"}
    ],
    "candidate_medication": {
      "name": "Ibuprofen",
      "dosage": "400mg"
    }
  }'
```

## Step 3 — Read the response

The most important fields to display immediately:

```json
{
  "headline": "Consider acetaminophen — ibuprofen may reduce lisinopril effectiveness.",
  "proceed": "caution",
  "risk_level": "medium"
}
```

- `headline` — show this prominently to the dentist
- `proceed` — colour-code: green=safe, amber=caution/modify, red=do_not_proceed
- `risk_level` — badge indicator

## Step 4 — Add procedure context

Adding the procedure improves the response with procedure-specific checks:

```json
{
  "patient": { "age": 54, "sex": "female", "conditions": ["hypertension"], "allergies": [] },
  "current_medications": [{"name": "Lisinopril", "dosage": "10mg"}],
  "candidate_medication": {"name": "Ibuprofen", "dosage": "400mg"},
  "procedure": {"type": "extraction", "complexity": "routine"}
}
```

## Step 5 — Handle errors

| Error | Cause | Fix |
|---|---|---|
| `401 INVALID_API_KEY` | Missing or wrong API key | Check `X-API-Key` header |
| `429 RATE_LIMIT_MINUTE` | Too many requests | Wait `retry_after_seconds` then retry |
| `422 VALIDATION_ERROR` | Bad request body | Check required fields and types |

## Next steps

See the [full integration guide](integration-guide.md) for complete field reference, response structure, and implementation guidance.
