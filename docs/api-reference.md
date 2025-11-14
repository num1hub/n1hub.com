# N1Hub Engine v0.1 — API Reference

**File:** `docs/api-reference.md`
**Version:** 0.1.0

---

## A. Introduction

The N1Hub Engine is a FastAPI service that ingests raw content, transforms it into **Knowledge Capsules** via the **DeepMine** pipeline, stores them, and serves **RAG** (Retrieval‑Augmented Generation) chat over selected scopes. The engine exposes REST endpoints for ingestion, jobs, capsules, chat, observability, validation, health, SSE, and admin utilities. Core modules live under `apps/engine/app/` (e.g., `main.py`, `pipeline.py`, `rag.py`, `vectorizer.py`, `store_pg.py`, validators, observability, errors, events, retention). 
High‑level behavior and features (DeepMine pipeline, strict citations, scopes, observability, SSE) are described in the project README. 

**Primary workflow**

1. **Ingest** content → creates an async job
2. **Monitor** job (poll or SSE)
3. **Read** the resulting capsule
4. **Chat** with RAG over selected scopes
   All endpoints and models below match v0.1 behavior. 

---

## B. Base URL

All endpoints are relative to your deployed Engine base URL.

* Local: `http://127.0.0.1:8000`
* Production: `https://<your-engine-domain>`


---

## C. Authentication

v0.1 does **not** require authentication. Rate limiting and job concurrency are enforced per client IP (derived from connection or `X-Forwarded-For`). 

---

## D. Rate Limiting

| Area                     | Limit | Window | Scope  |
| ------------------------ | ----: | -----: | ------ |
| **POST /ingest**         |    60 |  1 min | per IP |
| **POST /chat**           |    60 |  1 min | per IP |
| **Public scope queries** |   120 |  1 min | global |
| **Other endpoints**      |     — |      — | none   |

Additional limits:

* **Max concurrent jobs** per user: **10**
* **Max payload size**: **20 MB** (413 if exceeded)
* On 429, responses include `Retry-After` seconds. Optional headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`. 

---

## E. Content Ingestion API

### POST `/ingest`

Create an asynchronous job to process content through DeepMine and produce a Knowledge Capsule.

**Headers**

* `Idempotency-Key` *(optional)* — deduplicate retries. 

**Request — `IngestRequest`**

```json
{
  "title": "Introduction to Machine Learning",
  "content": "Machine learning is a subset of AI...",
  "tags": ["machine-learning", "ai", "fundamentals"],
  "include_in_rag": true,
  "author": "user",
  "language": "en",
  "source": { "type": "text", "uri": null },
  "privacy_level": "standard"
}
```

**Response — `200 OK`**

```json
{ "job_id": "01JAX0Z5Z5X6Z5Z5Z5Z5Z5Z5Z5", "state": "queued" }
```

**Errors**

* `413 Payload Too Large` (body > 20 MB)
* `429 Too Many Requests` (rate/concurrency)
* `403 Forbidden` (feature‑flagged ingestion types)
* `422 Unprocessable Entity` (invalid body)


---

## F. Job Management API

### GET `/jobs`

List recent ingestion jobs (desc by creation time).

**Response — `200 OK`**

```json
[
  {
    "id": "01JAX0Z5Z5X6Z5Z5Z5Z5Z5Z5Z5",
    "code": 200,
    "stage": "done",
    "state": "succeeded",
    "progress": 100,
    "created_at": "2025-11-13T18:30:00Z",
    "updated_at": "2025-11-13T18:30:30Z",
    "error": null,
    "capsule_id": "01JAX0Z5Z5X6Z5Z5Z5Z5Z5Z5Z6"
  }
]
```



### GET `/jobs/{job_id}`

Fetch a single job.

**Response — `200 OK`**

```json
{
  "id": "01JAX0Z5Z5X6Z5Z5Z5Z5Z5Z5Z5",
  "code": 170,
  "stage": "indexing",
  "state": "processing",
  "progress": 90,
  "created_at": "2025-11-13T18:30:00Z",
  "updated_at": "2025-11-13T18:30:25Z",
  "error": null,
  "capsule_id": null
}
```

**Errors**

* `404 Not Found` (unknown `job_id`)


### DELETE `/jobs/{job_id}`

Cancel a job **only** if it has **not** reached indexing (i.e., before code ≥ **170**).

**Response — `200 OK`**

```json
{ "status": "cancelled", "job_id": "01JAX0Z5Z5X6Z5Z5Z5Z5Z5Z5Z5" }
```

**Errors**

* `400 Bad Request` (already indexing or beyond)
* `404 Not Found` (unknown `job_id`)


**Job states, codes & stages**

| Code | Stage (typical)         | State                |
| ---: | ----------------------- | -------------------- |
|  100 | queued                  | `queued`             |
|  110 | ingesting / normalizing | `processing`         |
|  120 | segmenting              | `processing`         |
|  130 | extracting              | `processing`         |
|  140 | synthesizing            | `processing`         |
|  150 | assembling              | `processing`         |
|  160 | validating              | `processing`         |
|  170 | indexing                | `processing`         |
|  200 | done                    | `succeeded`          |
|  500 | failed/cancelled        | `failed`/`cancelled` |

Codes and stage names reflect pipeline progression validated by tests and SSE examples. 

---

## G. Capsule API

### GET `/capsules`

List Knowledge Capsules.

**Query**

* `include_in_rag` *(boolean, optional)* — filter by RAG inclusion.

**Response — `200 OK`** (abbrev. `CapsuleModel`)

```json
[
  {
    "include_in_rag": true,
    "metadata": {
      "capsule_id": "01JAX0Z5Z5X6Z5Z5Z5Z5Z5Z5Z6",
      "status": "active",
      "tags": ["machine-learning", "ai", "fundamentals"],
      "semantic_hash": "ml-ai-fundamentals-..."
    },
    "core_payload": { "content": "Machine learning is..." },
    "neuro_concentrate": {
      "summary": "70–140 word summary...",
      "keywords": ["machine-learning", "ai", "supervised", "unsupervised", "rl"],
      "semantic_hash": "ml-ai-fundamentals-..."
    },
    "recursive": { "links": [], "confidence": 0.92 }
  }
]
```



### GET `/capsules/{capsule_id}`

Fetch a single capsule by ID.

**Response — `200 OK`**

```json
{
  "include_in_rag": true,
  "metadata": { "...": "..." },
  "core_payload": { "...": "..." },
  "neuro_concentrate": { "...": "..." },
  "recursive": { "...": "..." }
}
```

**Errors**

* `404 Not Found` (unknown `capsule_id`)


### PATCH `/capsules/{capsule_id}`

Update capsule properties with audit logging.

**Request — `CapsulePatch`** *(all fields optional; at least one required)*

```json
{
  "include_in_rag": false,
  "tags": ["new-tag-1", "new-tag-2", "new-tag-3"],
  "status": "archived"
}
```

**Response — `200 OK`**
Returns the updated `CapsuleModel`.

**Errors**

* `400 Bad Request`: invalid updates (e.g., tags out of range or containing PII; invalid `status`)
* `404 Not Found` (unknown `capsule_id`)
  Validation rules and 4‑section capsule contract are enforced by the validator package. 

---

## H. Chat (RAG) API

### POST `/chat`

Submit a RAG query; returns grounded answers with strict citations.

**Request — `ChatRequest`**

```json
{
  "query": "What are the main types of machine learning?",
  "scope": ["my"]
}
```

**Scopes**

* `["my"]` *(default)* — user’s active RAG‑included capsules
* `["public"]` — active public capsules above threshold
* `["inbox"]` — recent (last 30 days) active RAG‑included capsules
* `["tag1", "tag2"]` — any capsules matching listed tags
  Strict citation behavior and scope profiles are part of the v0.1 reference implementation.  

**Response — `200 OK`** (`ChatResponse`)

```json
{
  "answer": "The main types are supervised, unsupervised, and reinforcement learning. 【01JAX0Z5Z5X6Z5Z5Z5Z5Z5Z5Z6】",
  "sources": ["01JAX0Z5Z5X6Z5Z5Z5Z5Z5Z5Z6"],
  "metrics": {
    "retrieval_recall": 1.0,
    "contextual_recall": 0.9,
    "ndcg": 1.0,
    "mrr": 1.0,
    "faithfulness": 0.98,
    "citation_share": 1.0,
    "router_health_score": 0.92
  }
}
```

**Fallback (insufficient context)**
If fewer than 2 distinct capsules support grounding:

```json
{
  "answer": "idk+dig_deep",
  "sources": [],
  "metrics": {}
}
```



---

## I. Observability API

Observability endpoints expose retrieval quality, router health, semantic hash integrity, and PII hygiene.  

### GET `/observability/retrieval`

Query params: `window_days` *(int, default 7, max 30)*

**Response — `200 OK`**

```json
{
  "name": "retrieval-faithfulness",
  "status": "ok",
  "details": "Search for the latest retrieval and faithfulness metrics...",
  "metrics": {
    "retrieval_recall": 0.9,
    "contextual_recall": 0.92,
    "ndcg": 0.88,
    "mrr": 0.85,
    "faithfulness": 0.95,
    "citation_share": 0.85
  }
}
```

### GET `/observability/router`

**Response — `200 OK`**

```json
{
  "name": "router-health",
  "status": "ok",
  "details": "Router diagnostics...",
  "metrics": {
    "router_health_score": 0.9,
    "route_diversity": 0.85,
    "single_capsule_dominance": 0.0,
    "anomaly_flags": 0
  }
}
```

### GET `/observability/semantic-hash`

**Response — `200 OK`**

```json
{
  "name": "semantic-hash-integrity",
  "status": "ok",
  "details": "Check mirrored semantic hashes for mismatches...",
  "metrics": {
    "semantic_hash_mismatch_rate": 0.0,
    "integrity_violations": 0
  }
}
```

### GET `/observability/pii`

**Response — `200 OK`**

```json
{
  "name": "pii-scan",
  "status": "ok",
  "details": "Capsules containing personal identifiers...",
  "metrics": { "pii_flagged_capsules": 0 }
}
```

### GET `/observability/standard`

Aggregates standard observability reports into a single list.
Optional: `window_days` for retrieval metrics (default 7).

**Response — `200 OK`**

```json
[
  { "name": "retrieval-faithfulness", "status": "ok", "details": "...", "metrics": { } },
  { "name": "router-health", "status": "ok", "details": "...", "metrics": { } },
  { "name": "semantic-hash-integrity", "status": "ok", "details": { }, "metrics": { } },
  { "name": "pii-scan", "status": "ok", "details": "...", "metrics": { } }
]
```



---

## J. Health & Readiness Endpoints

### GET `/healthz`

Component health (DB, Redis, pgvector).

**Response — `200 OK`**

```json
{
  "status": "ok",
  "timestamp": "2025-11-13T18:45:00Z",
  "components": {
    "database": { "status": "healthy" },
    "redis": { "status": "healthy" },
    "pgvector": { "status": "healthy" }
  }
}
```

Component statuses may also be `unhealthy`, `not_configured`, `not_applicable`. 

### GET `/readyz`

Readiness for orchestration (e.g., k8s).

**Response — `200 OK` (ready)**

```json
{
  "status": "ready",
  "timestamp": "2025-11-13T18:46:00Z",
  "components": {
    "database": { "status": "healthy", "schema_ready": true },
    "pgvector": { "status": "healthy" }
  }
}
```

**Response — `503 Service Unavailable` (not ready)**

```json
{
  "status": "not_ready",
  "timestamp": "2025-11-13T18:47:00Z",
  "components": {
    "database": { "status": "unhealthy", "schema_ready": false, "error": "..." },
    "pgvector": { "status": "unhealthy", "error": "pgvector extension not installed" }
  }
}
```



### GET `/livez`

Simple liveness probe.

**Response — `200 OK`**

```json
{ "status": "live", "timestamp": "2025-11-13T18:48:00Z" }
```



---

## K. Server‑Sent Events (SSE)

### GET `/events/stream`

Open a `text/event-stream` that emits real‑time job updates plus periodic heartbeats.

**Stream examples**

```
: heartbeat
data: {"job_id":"01JAX...","code":110,"stage":"normalizing","state":"processing","progress":15}

data: {"job_id":"01JAX...","code":200,"stage":"done","state":"succeeded","progress":100,"capsule_id":"01JAX..."}
: heartbeat
```

**Browser usage**

```js
const es = new EventSource(`${API_BASE}/events/stream`);
es.onmessage = (e) => {
  const update = JSON.parse(e.data);
  console.log('Job update', update);
};
```



---

## L. Validation API

### POST `/validate/capsule`

Validate a single capsule against the v0.1 contract and guardrails (can optionally auto‑fix non‑strict issues).

**Query**

* `strict_mode` *(boolean, default=false)* — disable auto‑fixes when `true`.

**Request — `CapsuleModel`**
*(Send a full capsule; see model in Section O.)*

**Response — `200 OK` (valid with auto‑fix)**

```json
{
  "ok": true,
  "errors": [],
  "warnings": [],
  "auto_fixes_applied": ["summary trimmed to 140 words"],
  "capsule": { /* auto-fixed capsule */ }
}
```

**Response — `200 OK` (invalid)**

```json
{
  "ok": false,
  "errors": [
    { "path": "/metadata/semantic_hash", "message": "Hash mismatch..." }
  ],
  "warnings": [],
  "auto_fixes_applied": [],
  "capsule": null
}
```



### POST `/validate/batch`

Validate a list of capsules in one call.

**Query**

* `strict_mode` *(boolean, default=false)*

**Request**

```json
[ { /* CapsuleModel */ }, { /* CapsuleModel */ } ]
```

**Response — `200 OK`**

```json
{
  "ok": true,
  "total": 10,
  "valid": 8,
  "invalid": 2,
  "total_errors": 3,
  "total_warnings": 5,
  "results": [
    {
      "capsule_id": "01HZ...",
      "ok": true,
      "errors": [],
      "warnings": [],
      "auto_fixes_applied": []
    }
  ]
}
```



---

## M. Admin API

### POST `/admin/seed/20-pack`

Seed the store with a 20‑pack capsule set (for demos/tests).

**Response — `200 OK`**

```json
{ "status": "seeded", "capsule_count": 20 }
```

**Errors**

* `404 Not Found` (20‑pack asset not found)


---

## N. Error Handling

**Standard error envelope**

```json
{ "detail": "Error message here" }
```

**HTTP status codes**

* `200 OK`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`,
  `413 Payload Too Large`, `422 Unprocessable Entity`,
  `429 Too Many Requests`, `500 Internal Server Error`, `503 Service Unavailable`
  On 429, responses include `Retry-After`. For 422, FastAPI validation details include `loc`, `msg`, `type`. 

**Job codes** (see Section F for mapping): **100–170**, **200**, **500**. 

---

## O. Data Models

### IngestRequest

```ts
{
  title: string;
  content: string;
  tags: string[];              // 3–10 lowercase items recommended
  include_in_rag: boolean;
  author?: string;
  language?: string;           // BCP‑47
  source?: { type: string; uri: string|null };
  privacy_level?: string;      // e.g., "standard"
}
```



### CapsuleModel (4‑section contract)

```ts
{
  include_in_rag: boolean;
  metadata: {
    capsule_id: string;        // ULID
    version?: string;
    status: "draft"|"active"|"archived";
    author?: string;
    created_at?: string;       // ISO‑8601 UTC
    language?: string;         // BCP‑47
    source?: { type: string; uri: string|null };
    tags: string[];            // 3–10 items
    length?: { chars: number; tokens_est: number };
    semantic_hash: string;     // mirrors neuro_concentrate.semantic_hash
  };
  core_payload: {
    content_type?: string;     // e.g., text/markdown
    content: string;
    truncation_note?: string|null;
  };
  neuro_concentrate: {
    summary: string;           // 70–140 words
    keywords: string[];        // ~5–12
    entities: any[];
    claims: any[];
    insights: any[];
    questions: any[];
    archetypes: any[];
    symbols: any[];
    emotional_charge?: number; // -1..1
    vector_hint?: string[];    // ~8–16
    semantic_hash: string;     // must match metadata.semantic_hash
  };
  recursive: {
    links: Array<{ rel: string; target_capsule_id: string; confidence: number; reason?: string }>;
    actions: any[];
    prompts: any[];
    confidence: number;        // 0..1
  };
}
```

Validated & auto‑fixed by `validators/capsule_validator.py`.  

### CapsulePatch

```ts
{
  include_in_rag?: boolean;
  tags?: string[];             // 3–10, PII‑free
  status?: "draft"|"active"|"archived";
}
```



### JobModel

```ts
{
  id: string;                  // ULID
  code: number;                // 100..170, 200, 500
  stage: string;
  state: "queued"|"processing"|"succeeded"|"failed"|"cancelled";
  progress: number;            // 0..100
  created_at: string;          // ISO‑8601 UTC
  updated_at: string;          // ISO‑8601 UTC
  capsule_id: string|null;
  error: {
    code: number;
    stage: string;
    issues: Array<{ path: string; message: string }>;
  } | null;
}
```



### ChatRequest / ChatResponse

```ts
// ChatRequest
{ query: string; scope?: string[]; } // ["my"] | ["public"] | ["inbox"] | ["tag", "..."]

// ChatResponse
{
  answer: string;              // "idk+dig_deep" fallback if insufficient grounding
  sources: string[];           // capsule_ids
  metrics?: {
    retrieval_recall?: number;
    contextual_recall?: number;
    ndcg?: number;
    mrr?: number;
    faithfulness?: number;
    citation_share?: number;
    router_health_score?: number;
  };
}
```



### ObservabilityReport

```ts
{
  name: string;                // e.g., "retrieval-faithfulness", "router-health"
  status: "ok"|"warn"|"error";
  details: string;
  metrics: Record<string, number>;
}
```



### Module layout (reference)

Engine modules implementing the above endpoints and behaviors:

* `apps/engine/app/main.py` (FastAPI routes)
* `apps/engine/app/pipeline.py` (DeepMine pipeline)
* `apps/engine/app/rag.py` (retrieval & answerer)
* `apps/engine/app/vectorizer.py` (semantic embeddings)
* `apps/engine/app/store_pg.py` (Postgres/pgvector)
* `apps/engine/app/validators/*`, `observability/*`, `errors/*`, `events/*`, `retention/*`


---

## P. Examples

### End‑to‑end workflow (bash)

```bash
# 1) Ingest
JOB_ID=$(curl -sS -X POST "$API/ingest" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "title": "ML Basics",
    "content": "Machine learning is ...",
    "tags": ["ml","ai","basics"],
    "include_in_rag": true
  }' | jq -r '.job_id')

# 2) Poll job until done
while true; do
  STATE=$(curl -s "$API/jobs/$JOB_ID" | jq -r '.state')
  [ "$STATE" = "succeeded" ] && break
  [ "$STATE" = "failed" ] && { echo "failed"; exit 1; }
  sleep 1
done

# 3) Get capsule_id
CAPSULE_ID=$(curl -s "$API/jobs/$JOB_ID" | jq -r '.capsule_id')

# 4) Chat
curl -sS -X POST "$API/chat" -H "Content-Type: application/json" -d "{
  \"query\": \"What is this about?\",
  \"scope\": [\"my\"]
}"
```



### Using SSE (browser)

```js
const es = new EventSource(`${API}/events/stream`);
es.onmessage = (e) => {
  const j = JSON.parse(e.data);
  if (j.job_id === JOB_ID) console.log(j.stage, j.progress);
};
```



### Capsule updates

```bash
curl -X PATCH "$API/capsules/$CAPSULE_ID" \
  -H "Content-Type: application/json" \
  -d '{"status":"active","tags":["ml","ai","basics"]}'
```



---

## Q. Best Practices

* **Use `Idempotency-Key`** for ingestion to avoid duplicates on retry.
* **Prefer SSE** (`/events/stream`) or polling `/jobs/{id}` for progress.
* **Handle 429** with exponential backoff; read `Retry-After`.
* **Choose the right RAG scope**: `["my"]` by default; `["public"]`, `["inbox"]`, or tag scopes as needed.
* **Keep tags clean** (3–10, lowercase, no PII).
* **Monitor observability** endpoints regularly.
* **Update docs & env** if you change behavior/config (see contributing guide).  

---

## R. Support

* **Project overview & quickstart** — see README. 
* **Issues & questions** — open a GitHub Issue on the repository. 
* **Health checks** — `/healthz`, `/readyz`, `/livez` on your engine base URL. 

---

### Appendix — Pipeline Stages (DeepMine)

Typical stage breakdown reflected in job codes:

1. **Queued** (100)
2. **Ingesting/Normalizing** (110)
3. **Segmenting** (120)
4. **Extracting** (130)
5. **Synthesizing** (140)
6. **Assembling** (150)
7. **Validating** (160)
8. **Indexing** (170)
9. **Done** (200)
   Failures map to **500** with error details. The pipeline is implemented in `pipeline.py` and related modules.  

---

**End of `docs/api-reference.md`.**
