# Chitra.ai — Architecture

AI video analysis service. It receives a captured video frame (image) plus an
audio clip, transcribes the audio, analyses the image + transcript with an LLM,
generates a report, and emails it. Built as a small **multi-agent pipeline**
behind a FastAPI HTTP API.

---

## 1. High-level overview

```
   Client (browser / caller)
        │  POST /analyze  { image_base64, audio_transcription, timestamp }
        ▼
   ┌──────────────────────── FastAPI app (app/main.py) ───────────────────────┐
   │  CORS · routing · request validation                                     │
   │                                                                          │
   │   API layer (app/api)          Agent pipeline (app/agents)               │
   │   ┌────────────┐   calls   ┌──────────────┐  ┌───────────┐  ┌──────────┐ │
   │   │ analyze.py │ ────────► │ DataCapture  │─►│ Analysis  │─►│  Report  │ │
   │   │ health.py  │           │   Agent      │  │  Agent    │  │  Agent   │ │
   │   └────────────┘           └──────┬───────┘  └─────┬─────┘  └────┬─────┘ │
   └──────────────────────────────────┼───────────────┼─────────────┼────────┘
                                       ▼               ▼             ▼
                                  OpenAI Whisper   OpenAI GPT-4o   SendGrid
                                  (transcribe)     (vision+text)   (email)
```

**Design principle:** the app is **stateless** — it stores nothing locally
between requests. All state lives in external services (OpenAI, SendGrid). This
is what lets us run many identical copies behind a load balancer to scale.

---

## 2. Project structure

```
chitra.ai/
├── app/
│   ├── main.py            # FastAPI app: CORS, router registration (the `app` object)
│   ├── config.py          # Single source of config: env vars, logger, shared clients
│   ├── api/               # HTTP layer — thin routers, no business logic
│   │   ├── analyze.py     #   POST /analyze, GET /
│   │   └── health.py      #   GET /health  (cheap, no billed calls)
│   ├── agents/            # Business logic — one agent per pipeline stage
│   │   ├── data_capture.py#   validate image + transcribe audio (Whisper)
│   │   ├── analysis.py    #   vision + text analysis, scoring (GPT-4o)
│   │   ├── report.py      #   build HTML report + send email (SendGrid)
│   │   └── workflow.py    #   orchestrates the three agents in sequence
│   └── models/
│       └── schemas.py     # Pydantic models = the data contracts between stages
├── templates/index.html   # Minimal landing page served at GET /
├── tests/test_smoke.py    # Smoke tests run in CI
├── Dockerfile             # How the production image is built
├── docker-compose.yml     # One-command local/single-server run
├── .github/workflows/ci.yml  # CI/CD pipeline
└── requirements*.txt      # runtime + dev dependencies
```

**Layering rule:** `api → agents → config/models`. The API layer only handles
HTTP concerns and delegates to agents; agents hold the logic; `config` and
`models` are shared foundations. This keeps each layer independently testable.

---

## 3. Application components

### Config (`app/config.py`)
Loads all configuration from environment variables **once** at startup and
exposes the shared, long-lived objects:
- the async **OpenAI client** (with a 30s timeout + 2 retries so a slow API call
  can't tie up a worker),
- the **logger** (writes to stdout so containers/log collectors capture it),
- `templates`, and the parsed `CORS_ORIGINS` list.

Nothing else reads the environment directly — every module imports from here.

### Models (`app/models/schemas.py`)
Pydantic models are the **contracts** that flow between stages:
`VideoData` (request in) → `CapturedData` → `AnalysisResult` → `AnalysisReport`
(response out). They give automatic request validation (a bad body → HTTP 422)
and a single definition of each shape.

### API layer (`app/api/`)
Thin FastAPI routers, registered in `main.py` via `include_router`:
- `analyze.py` — `POST /analyze` (runs the pipeline) and `GET /` (landing page).
- `health.py` — `GET /health`, deliberately cheap and dependency-free so a load
  balancer can poll it frequently **without triggering billed API calls**.

### Agent pipeline (`app/agents/`)
Each agent owns one stage; `workflow.py` chains them:

```
process_video_analysis_workflow(image, audio, timestamp)
   1. DataCaptureAgent  → validate image, transcribe audio (Whisper) → CapturedData
   2. AnalysisAgent     → GPT-4o vision+text, produce score/priority  → AnalysisResult
   3. ReportAgent       → render HTML report, email via SendGrid       → AnalysisReport
```

Adding a stage = add an agent + a line in the workflow. The API layer never
changes.

---

## 4. Request lifecycle

```
POST /analyze
  → FastAPI validates body against VideoData  (invalid → 422, no work done)
  → workflow step 1: DataCaptureAgent
        · validate_image()      quick sanity check
        · process_audio()       base64 → temp file → Whisper → transcript
  → workflow step 2: AnalysisAgent
        · GPT-4o with image + transcript → JSON → AnalysisResult (score, priority…)
  → workflow step 3: ReportAgent
        · generate_html_report() → send_report() via SendGrid
  → 200 JSON { analysis, session_id, priority_level, score, email_sent, … }
Errors anywhere → logged → HTTP 500 with a message (see analyze.py)
```

---

## 5. Runtime / serving model

The app is an **ASGI application** (`app.main:app`). How it's launched differs
by environment:

| | Local dev | Production (Docker) |
|---|---|---|
| Server | `uvicorn app.main:app --reload` | `gunicorn app.main:app` |
| Processes | 1, auto-reloads on file save | N workers (`WEB_CONCURRENCY`), stable |
| Purpose | fast feedback loop | multi-core throughput + worker restarts |

**Gunicorn** is a process manager that runs several **Uvicorn workers** (each an
independent copy of the app) and load-balances across them, so one box uses all
its CPU cores and a crashed worker is auto-restarted.

```
        requests ─► Gunicorn ─┬─ uvicorn worker 1 (app)
                              ├─ uvicorn worker 2 (app)
                              ├─ uvicorn worker 3 (app)
                              └─ uvicorn worker 4 (app)
```

---

## 6. Containerization (Docker)

The `Dockerfile` builds a single portable **image** — OS + Python + deps + code:

```
FROM python:3.13-slim         # minimal base with Python
COPY requirements.txt         # deps copied first…
RUN  pip install …            # …so this slow layer is cached across code edits
COPY . .                      # then the app code
USER appuser                  # run as non-root (security)
CMD  gunicorn app.main:app …  # start N workers on port 8000
```

- **`.dockerignore`** keeps `.venv`, `.git`, `.env`, tests and CI files out of
  the image (smaller image; secrets never baked in).
- **`docker-compose.yml`** records the run settings (port mapping, `.env`
  injection, restart policy, `/health` healthcheck) so local/single-server runs
  are one command: `docker compose up --build`.

**Config is injected at runtime, never built in.** Secrets come from env vars
(`--env-file` locally, the platform's secret store in prod). The same image runs
in every environment; only the injected config changes.

---

## 7. Deployment & environments

### Promotion model — build once, promote the same image

```
   git push (main)
        │  CI builds ONE image, tagged with the commit SHA
        ▼
   ghcr.io/amanmulani09/chitra.ai:<sha>      (container registry)
        │
        ├──────────────► UAT   : image:<sha> + UAT secrets  (1–2 replicas)
        │   (auto)
        │
        └── ⏸ approval ─► PROD  : image:<sha> + PROD secrets (N replicas)
            (same bytes UAT tested → prod)
```

The **same image artifact** is deployed to UAT and Prod. Only the **config**
differs per environment (kept as secrets in each environment, never in git):

| Setting | UAT | Prod |
|---|---|---|
| `OPENAI_API_KEY` | test key | prod key |
| `SENDGRID_API_KEY` / emails | test | prod |
| `CORS_ORIGINS` | `https://uat.chitra.ai` | `https://chitra.ai` |
| `WEB_CONCURRENCY` / replicas | small | larger |

### CI/CD pipeline (`.github/workflows/ci.yml`)

```
 push/PR ─► [test] ─► [build+push image] ─► [deploy UAT] ─► ⏸ approval ─► [deploy PROD]
            always     on main only          auto                         same image
```

1. **test** — runs `pytest` smoke tests on every push and PR; gates everything.
2. **build** — builds the image once, tags `:<sha>` + `:latest`, pushes to
   GitHub Container Registry (`ghcr.io`).
3. **deploy-uat** — deploys `:<sha>` to UAT automatically (GitHub Environment
   `uat` holds UAT secrets).
4. **deploy-prod** — deploys the **same** `:<sha>` to Prod, gated behind a manual
   approval (GitHub Environment `prod` with required reviewers).

> The actual deploy commands are host-specific placeholders in the workflow —
> fill in whichever applies (Cloud Run / ECS / Kubernetes `kubectl set image`).

### Production topology (target: ~10K users)

Run on a managed container platform (Cloud Run, AWS ECS/Fargate, or Kubernetes):

```
                Internet
                   │  HTTPS
            ┌──────▼───────┐
            │ Load Balancer│   terminates TLS, spreads traffic, polls /health
            └──┬───┬───┬───┘
               ▼   ▼   ▼
           ┌─────┐┌─────┐┌─────┐
           │ ctr ││ ctr ││ ctr │   identical containers from image:<sha>
           │4 wkr││4 wkr││4 wkr│   (a "pod" each under Kubernetes)
           └─────┘└─────┘└─────┘
               │ external calls
               ▼
        OpenAI (Whisper, GPT-4o) · SendGrid
```

- **Horizontal scaling** — because the app is stateless, add/remove identical
  containers freely; the platform autoscales on load.
- **Health checks** — the platform polls `/health`; unhealthy containers are
  killed and replaced automatically (zero downtime).
- **Secrets** — stored in the platform's secret manager per environment, injected
  as env vars at runtime.

### Real-world bottleneck

At scale the constraint is **OpenAI** (rate limits + latency), not the app
itself. When those limits bite, the next architectural step is to make `/analyze`
**asynchronous**: enqueue the job (e.g. Redis/queue + worker), return a job ID
immediately, and deliver the report when ready — instead of holding the HTTP
request open for the full LLM round-trip.

---

## 8. Configuration reference

All config is environment variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Whisper transcription + GPT-4o analysis |
| `SENDGRID_API_KEY`, `FROM_EMAIL`, `RECIPIENT_EMAIL` | report email delivery |
| `CORS_ORIGINS` | comma-separated allowed origins (default `*`) |
| `LOG_LEVEL` | logging verbosity (default `INFO`) |
| `WEB_CONCURRENCY` | gunicorn worker count (default `4`) |
