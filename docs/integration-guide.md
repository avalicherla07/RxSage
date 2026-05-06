# RxSage API Integration Guide

Complete reference for integrating RxSage into dental practice management software.

---

## 1. Overview

RxSage is a clinical decision support API for US dental professionals. It receives patient data, current medications, and a candidate drug or anesthetic, then returns a structured clinical analysis organized in the order a dentist thinks at the chair: immediate flags, anesthetic safety, antibiotic safety, analgesic safety, sedation assessment, oral manifestations, and procedure-specific considerations.

RxSage returns a complete structured JSON response. The calling system is responsible for how that response is displayed to the dentist. RxSage does not have a user interface.

## 2. Base URL and Versioning

```
Production:  https://api.rxsage.com/v1
Sandbox:     https://sandbox.rxsage.com/v1  (coming soon)
```

All endpoints are versioned at `/v1`. Breaking changes will be introduced at `/v2` with advance notice. Existing `/v1` integrations will continue working during any transition period.

## 3. Authentication

Every request must include an API key:

```
X-API-Key: rsk_live_your_key_here
```

- Keys are provisioned by RxSage — contact api@rxsage.com
- One key per integration system
- Never expose keys in frontend code or logs
- If compromised, contact support@rxsage.com immediately

Missing or invalid key response:
```json
{"error": "Invalid or missing API key", "code": "INVALID_API_KEY"}
```

## 4. Rate Limits

```
10 requests per minute
100 requests per hour
500 requests per day
```

Response headers on every successful request:
```
X-RateLimit-Limit-Minute: 10
X-RateLimit-Remaining-Minute: 8
X-RateLimit-Limit-Hour: 100
X-RateLimit-Remaining-Hour: 97
```

Rate limit exceeded response:
```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_MINUTE",
  "message": "Maximum 10 requests per minute allowed.",
  "retry_after_seconds": 60
}
```

Use `retry_after_seconds` to implement backoff in your calling system.

## 5. The Analyze Endpoint

### 5.1 Method

```
POST /v1/analyze
Content-Type: application/json
X-API-Key: your_api_key_here
```

### 5.2 Required Fields

| Field | Type | Constraints | Description |
|---|---|---|---|
| `patient.age` | integer | 0–120 | Patient age in years |
| `patient.sex` | string | "male", "female", "other" | Biological sex |
| `patient.conditions` | string[] | Can be `[]` | Active medical conditions |
| `patient.allergies` | string[] | Can be `[]` | Known drug allergies |
| `current_medications` | object[] | Min 1 item | Current medications |
| `current_medications[].name` | string | Non-empty | Drug name (brand or generic) |
| `candidate_medication` | object | Required | Drug being considered |
| `candidate_medication.name` | string | Non-empty | Candidate drug name |

### 5.3 Optional Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `current_medications[].dosage` | string | null | e.g. "5mg" |
| `candidate_medication.dosage` | string | null | Dosage being considered |
| `procedure` | object | null | Dental procedure context |
| `procedure.type` | string | null | "extraction", "implant", "filling", "root_canal", "scaling", "sedation", "crown" |
| `procedure.complexity` | string | null | "routine", "surgical", "complex" |
| `supplements` | object[] | `[]` | Herbal/vitamin supplements |
| `supplements[].name` | string | — | Supplement name |
| `supplements[].dose` | string | null | Dose if known |
| `sedation_requested` | boolean | false | True if patient requested sedation |
| `sedation_agent_requested` | string | null | e.g. "Valium" |
| `additional_notes` | string | null | Any other clinical context |

### 5.4 Drug Name Handling

RxSage accepts both brand and generic names and normalizes automatically:

```
"Warfarin"                    → warfarin
"WARFARIN (COUMADIN)"         → warfarin
"warfarin 5mg"                → warfarin
"Coumadin"                    → warfarin
"Tylenol"                     → acetaminophen
"ibuprofen 400mg TID"         → ibuprofen
```

The normalized name is returned in `normalised_drug_names` when a change was made.


## 6. Response Structure

### 6.1 Tier 1 — Immediate

Always present, always non-empty. Surface these first.

| Field | Type | Description |
|---|---|---|
| `headline` | string | One sentence — the most important clinical finding |
| `proceed` | string | "safe", "caution", "modify", "do_not_proceed" |
| `risk_level` | string | "high", "medium", "low" |
| `flags` | array | Badge-style alerts with label and severity |

### 6.2 Tier 2 — Workflow Sections

Clinical assessment in dentist workflow order. Always present — empty lists when no findings.

| Section | Description |
|---|---|
| `anesthetic_safety` | Recommended anesthetic, epinephrine status, cartridge limits |
| `antibiotic_safety` | Prophylaxis assessment, candidate safety, alternatives |
| `analgesic_safety` | First-line pain management, NSAID/acetaminophen status |
| `sedation_safety` | Nitrous oxide note, oral sedation status, alternatives |
| `oral_manifestations` | Oral side effects of current medications |
| `procedure_context` | Procedure-specific checks and modifications |

### 6.3 Tier 3 — Clinical Detail

| Field | Type | Description |
|---|---|---|
| `clinical_explanation` | string | Full mechanism-based explanation |
| `patient_risk_factors` | array | Which patient factors elevated risk |
| `physician_referral` | string/null | When and why to consult |
| `monitoring_recommendations` | array | Post-procedure monitoring steps |
| `reasoning_layers_used` | array | Data sources that contributed |
| `sources` | array | Evidence sources with attribution |
| `evidence_quality` | object | "strong", "moderate", or "limited" with reason |
| `confidence` | string | "high", "medium", "low" |

### 6.4 Meta Fields

| Field | Type | Description |
|---|---|---|
| `request_id` | string | Unique ID — use for support queries |
| `cache_hit` | boolean | True if served from cache |
| `normalised_drug_names` | array | Drug names that were normalized |
| `drugs_not_found` | array | Drug names that could not be matched |
| `fallback` | boolean | True if AI reasoning failed |
| `fallback_reason` | string/null | Why fallback was triggered |

## 7. Complete Example

See [docs/examples/basic-request.json](examples/basic-request.json) and [docs/examples/basic-response.json](examples/basic-response.json) for a full request/response pair.

## 8. Error Reference

| HTTP | Code | Meaning | Action |
|---|---|---|---|
| 400 | `VALIDATION_ERROR` | Bad request body | Fix required fields |
| 401 | `MISSING_API_KEY` | No X-API-Key header | Add the header |
| 401 | `INVALID_API_KEY` | Key not recognized | Contact api@rxsage.com |
| 429 | `RATE_LIMIT_MINUTE` | 10/min exceeded | Wait `retry_after_seconds` |
| 429 | `RATE_LIMIT_HOUR` | 100/hr exceeded | Wait `retry_after_seconds` |
| 429 | `RATE_LIMIT_DAY` | 500/day exceeded | Wait until next day |
| 500 | `INTERNAL_ERROR` | Server error | Report `request_id` to support |

Error format:
```json
{"error": "Human readable message", "code": "MACHINE_READABLE_CODE"}
```

Always log `request_id` from error responses — required when contacting support.


## 9. Implementation Guidance

### 9.1 When to Call RxSage

Call at the point of prescribing — when the dentist selects a medication or anesthetic. Not during intake. Not proactively.

```
1. Dentist selects candidate medication in your system
2. Your system collects: age, sex, conditions, allergies,
   current medications from the patient record
3. POST /v1/analyze with this data
4. Display: headline + proceed flag immediately (Tier 1)
5. Show workflow sections in sidebar/modal (Tier 2)
6. Full detail available on tap/click (Tier 3)
7. Dentist makes the prescribing decision
```

### 9.2 Displaying the Proceed Flag

| Value | UI Treatment |
|---|---|
| `safe` | Green indicator — proceed normally |
| `caution` | Amber indicator — proceed with awareness |
| `modify` | Amber indicator — show `procedure_modifications` |
| `do_not_proceed` | Red indicator — show `physician_referral` |

### 9.3 Handling Fallback Responses

When `fallback: true`:
- AI reasoning did not complete
- Raw verified data is still present
- Display: "Analysis based on verified drug data only"
- Do not suppress — raw data is still useful

### 9.4 Handling drugs_not_found

When non-empty:
- One or more drugs could not be matched
- Display the unmatched names to the dentist
- Advise manual verification
- Analysis continues but may be incomplete

### 9.5 Caching

Identical requests are cached for 24 hours. When `cache_hit: true`:
- Response is instant
- Content is identical to original
- Optionally show a "cached" indicator
- No action required — handled server-side

## 10. Clinical Disclaimer

RxSage is a clinical decision support tool. It is designed to assist dental professionals in making informed prescribing decisions — not to replace clinical judgment. All prescribing decisions remain the sole responsibility of the licensed dental professional. RxSage output should be reviewed by a qualified clinician before any clinical action is taken.

RxSage is not a medical device and has not been cleared by the FDA for diagnostic use. Integrating systems are responsible for ensuring their use of RxSage complies with applicable regulations and standards of care in their jurisdiction.

## 11. Support

```
API status:    https://status.rxsage.com  (coming soon)
Documentation: https://docs.rxsage.com   (coming soon)
Support:       support@rxsage.com
New API keys:  api@rxsage.com
```

When contacting support always include:
- Your API key ID (not the key itself)
- The `request_id` from the response
- The timestamp of the request
