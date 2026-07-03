# CODEBASE_ANALYSIS.md

## Why this repo is “messy”
You have a multi-service backend, but the repository also contains multiple duplicated/experimental copies of service folders under `AI/*`. Additionally, you have partially duplicated wiring inside service `main.py` files (router includes + alias routes), which strongly suggests copy/paste evolution.

## Canonical workflow (entrypoints)
From your root README and the files you pasted:

### 1) Authentication
- Entrypoint: `Authentication/index.js`
- Workflow: Express routes under `/auth` and `/emergency`.
- Keep: `Authentication/`

### 2) Location & SOS
- Entrypoint: `Location_S/app/main.py`
- Workflow: FastAPI includes `routes/location_routes.py` and `routes/sos_routes.py`.
- Keep: `Location_S/`

### 3) Notification Delivery (durable async)
- Entrypoint: `notofication/main.py`
- Workflow:
  - `POST /api/v1/alert/send` → persist + enqueue (RQ)
  - `POST /api/v1/status` → heartbeat/presence update
  - Worker runs delivery logic from `notofication/services/delivery.py`
- Keep: `notofication/`

### 4) Spring Boot (`shieldx/`)
- Keep: `shieldx/`

### 5) AI folders
- Under `AI/` you have repeated service structures:
  - `AI/Location_S/`
  - `AI/notofication/`
  - `AI/Route_S/`
  - `AI/Perodic_S/`
  - `AI/Gateway_S/`
  - `AI/Chatbot_S/`

These appear to be duplicates/copies because their folder names and internal `main.py` router wiring patterns match the canonical services.

## What I cannot complete “exactly” yet
To tell you **exactly which files to keep/remove aligned to workflow**, I must confirm which files are actually imported/referenced by the canonical entrypoints.

That requires repo-wide reference scanning (e.g., `rg`, ripgrep). Your environment currently fails `search_files` because `rg` (ripgrep) is not available / cannot be executed via the tool.

I attempted to verify `rg` availability via `where rg`, but it returned no usable path output, which indicates `rg` is not installed or not available in PATH.

## Provisional recommendation (high confidence, but not 100% proven)
- Keep (canonical):
  - `Authentication/`
  - `Location_S/`
  - `notofication/`
  - `shieldx/`
- Archive/remove (likely duplicates):
  - `AI/Location_S/`
  - `AI/notofication/`
  - `AI/Route_S/`
  - `AI/Perodic_S/`

## Required next step (to make it exact)
Install ripgrep and/or enable repo-wide search so I can compute a true dependency graph:
- from each canonical entrypoint (`Authentication/index.js`, `Location_S/app/main.py`, `notofication/main.py`, `shieldx/src/main/java/...`) 
- follow imports/references
- produce an exact keep/remove/archive list with justification per file.

