# How to Run — Project PUF

[← Back to Index](index.md)

This guide covers everything needed to get Project PUF running locally on **Windows**. All commands are shown for both **PowerShell** (recommended) and **CMD** where they differ.

---

## Prerequisites

| Tool | Version | Install | Check |
|------|---------|---------|-------|
| Python | ≥3.12 | [python.org](https://www.python.org/downloads/) or `winget install Python.Python.3.12` | `python --version` |
| Docker Desktop | Latest | [docker.com](https://www.docker.com/products/docker-desktop/) or `winget install Docker.DockerDesktop` | `docker compose version` |
| Node.js | ≥18 | [nodejs.org](https://nodejs.org/) or `winget install OpenJS.NodeJS.LTS` | `node --version` |
| Git | Any recent | [git-scm.com](https://git-scm.com/) or `winget install Git.Git` | `git --version` |
| Make | GNU Make | See [Make on Windows](#make-on-windows) below | `make --version` |

### Docker Desktop Setup

1. Install Docker Desktop with the **WSL 2 backend** (recommended) or Hyper-V backend
2. Open Docker Desktop and ensure the engine is running (whale icon in system tray)
3. In Docker Desktop Settings → Resources → WSL Integration, enable your default distro if using WSL 2

### Make on Windows

The project uses a `Makefile` for common commands. You have three options:

**Option A — Install Make via Chocolatey (recommended):**

```powershell
choco install make
```

**Option B — Install Make via Scoop:**

```powershell
scoop install make
```

**Option C — Skip Make entirely:**

Every `make` target is just a shell command. This guide shows the underlying commands alongside the `make` shortcuts so you can run them directly.

---

## Quick Start (5 Commands)

```powershell
# 1. Install Python dependencies
pip install -e ".[dev]"

# 2. Copy environment file
copy .env.example .env

# 3. Start all Docker services (PostgreSQL, PgBouncer, Prefect, API, Frontend)
docker compose -f config/docker-compose.yml up -d

# 4. Run database migrations (set password first)
$env:PUF_DB_PASSWORD = "puf_dev_password"
alembic -c pipelines/alembic/alembic.ini upgrade head

# 5. Verify everything is healthy
curl http://localhost:8000/health
```

After these 5 steps, the platform is running at:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Prefect UI | http://localhost:4200 |

---

## Step-by-Step Setup

### 1. Clone and Enter the Repository

```powershell
git clone <repository-url>
cd project_puf
```

### 2. Set Up Python Environment

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv

# Activate (PowerShell)
.venv\Scripts\Activate.ps1

# Activate (CMD)
# .venv\Scripts\activate.bat

# Install with dev dependencies (pytest, ruff, mypy, pre-commit)
pip install -e ".[dev]"
pre-commit install

# Or install production only
pip install -e .
```

> **PowerShell execution policy**: If `.ps1` activation fails, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once.

With Make installed, this simplifies to:

```powershell
make dev       # same as pip install -e ".[dev]" && pre-commit install
make install   # same as pip install -e .
```

### 3. Configure Environment Variables

```powershell
# PowerShell
copy .env.example .env
```

```cmd
:: CMD
copy .env.example .env
```

The `.env` file contains:

```dotenv
# PostgreSQL
PUF_DB_HOST=localhost
PUF_DB_PORT=5432
PUF_DB_NAME=puf
PUF_DB_PASSWORD=puf_dev_password
PUF_PGBOUNCER_PORT=6432

# Prefect
PREFECT_API_URL=http://localhost:4200/api
```

For local development, the defaults work out of the box. Only edit if you need custom ports or credentials.

### 4. Start Docker Services

```powershell
# With Make
make up

# Without Make
docker compose -f config/docker-compose.yml up -d
```

This starts 6 containers via `config/docker-compose.yml`:

| Container | Image | Port | Status |
|-----------|-------|------|--------|
| `puf-postgres` | `postgres:16-alpine` | 5432 | Health-checked (`pg_isready`) |
| `puf-pgbouncer` | `bitnami/pgbouncer` | 6432 | Waits for postgres |
| `puf-prefect-server` | `prefecthq/prefect:3-latest` | 4200 | Waits for postgres |
| `puf-prefect-worker` | `prefecthq/prefect:3-latest` | — | Waits for prefect-server |
| `puf-api` | Custom (Dockerfile.api) | 8000 | Waits for postgres |
| `puf-frontend` | Custom (frontend/Dockerfile) | 3000 | Waits for api |

Wait for all containers to become healthy:

```powershell
# Watch container status
docker compose -f config/docker-compose.yml ps

# Tail logs
docker compose -f config/docker-compose.yml logs -f
# Or: make logs
```

### 5. Run Database Migrations

Alembic reads `PUF_DB_PASSWORD` via `%(PUF_DB_PASSWORD)s` interpolation in `alembic.ini`. The variable must be set before running migrations.

```powershell
# PowerShell — set env var for this session
$env:PUF_DB_PASSWORD = "puf_dev_password"

# Run all 10 migrations
alembic -c pipelines/alembic/alembic.ini upgrade head
# Or: make migrate
```

```cmd
:: CMD — set env var for this session
set PUF_DB_PASSWORD=puf_dev_password

alembic -c pipelines/alembic/alembic.ini upgrade head
```

This creates:
- 7 database schemas (`catalog`, `reference`, `staging`, `intermediate`, `mart`, `metadata`, `raw`)
- 4 RBAC roles (`puf_pipeline`, `puf_dbt`, `puf_api`, `puf_admin`)
- 7 catalog tables, reference tables, staging tables, and all Tier 2 tables

Verify:

```powershell
alembic -c pipelines/alembic/alembic.ini current
# Or: make migrate-status
# Should show: head at revision 010
```

### 6. Verify the Stack

```powershell
# API health check
curl http://localhost:8000/health
# → {"status":"healthy","postgres":true,"duckdb":true,"version":"0.1.0"}

# Or in PowerShell without curl:
Invoke-RestMethod http://localhost:8000/health

# Open browser to services
Start-Process http://localhost:4200    # Prefect UI
Start-Process http://localhost:3000    # Frontend
Start-Process http://localhost:8000/docs  # API Swagger docs
```

---

## Loading Data

### Load Reference Data (First Time)

Reference data (FIPS codes, ICD-10, HCPCS, NDC, taxonomy, fee schedules) should be loaded first:

```powershell
python -m flows.reference_flow
```

This runs 14 reference source pipelines in two phases:
1. **Phase 1** (parallel): 11 geographic + code system sources
2. **Phase 2** (sequential): 3 fee schedule sources (depend on Phase 1)

### Load Provider Data

```powershell
# NPPES providers (~8M rows, ~4GB download)
python -m flows.nppes_flow

# Provider of Services facilities
python -m flows.pos_flow

# Hospital cost reports
python -m flows.cost_reports_flow
```

### Load Utilization Data + Transform + Export

The master flow handles Part B, Part D, and Geographic Variation, then runs dbt and exports Parquet:

```powershell
# Full refresh for data year 2022
python -m flows.utilization_flow --data-year 2022
```

This runs:
1. **Phase 1**: Part B + Part D + GeoVar pipelines in parallel
2. **Phase 2**: `dbt run` (staging → intermediate → mart)
3. **Phase 3**: Export mart tables to Parquet for DuckDB

Or run individual utilization pipelines:

```powershell
python -m flows.partb_flow --data-year 2022
python -m flows.partd_flow --data-year 2022
python -m flows.geovar_flow --data-year 2022
```

### Run dbt Models Manually

```powershell
# Set dbt password
$env:PUF_DBT_PASSWORD = "puf_dbt_password"

# Run all models
cd models
dbt run
cd ..

# Or with Make
make dbt-run

# Run specific tags
cd models
dbt run --select tag:intermediate tag:mart
cd ..

# Test all models
make dbt-test
```

dbt uses profile `project_puf` defined in `models/profiles.yml`. The `puf_dbt` role needs password `PUF_DBT_PASSWORD` (defaults to `puf_dbt_password`).

---

## Development Workflow

### Running Tests

```powershell
# Fast: unit tests only (excludes integration)
pytest -m "not integration" -v
# Or: make test

# Full: all tests including integration
pytest -v
# Or: make test-all

# With coverage report
pytest -m "not integration" --cov=pipelines --cov=flows --cov=api --cov-report=term-missing
# Or: make test-cov
```

Current status: 258 tests, 258 passed, 11 skipped.

### Code Quality

```powershell
# Lint
ruff check .
# Or: make lint

# Auto-format
ruff format .
ruff check --fix .
# Or: make format

# Type check
mypy pipelines/ flows/ api/
# Or: make typecheck
```

### Database Access

```powershell
# Open psql shell via Docker
docker compose -f config/docker-compose.yml exec postgres psql -U puf_admin -d puf
# Or: make db-shell

# Then explore:
# \dn                          -- list schemas
# \dt catalog.*                -- list catalog tables
# SELECT count(*) FROM catalog.sources;
```

### Frontend Development (Outside Docker)

For faster iteration with hot reload:

```powershell
cd frontend

# Install dependencies
npm install

# Start dev server (requires API at localhost:8000)
npm run dev
```

The frontend at http://localhost:3000 expects the API at `http://localhost:8000/api/v1` (configured via `NEXT_PUBLIC_API_URL`).

### API Development (Outside Docker)

```powershell
# Run API directly (requires PostgreSQL + data loaded)
uvicorn api.main:app --reload --port 8000
```

---

## Stopping and Cleaning Up

```powershell
# Stop all Docker services (preserves data)
docker compose -f config/docker-compose.yml down
# Or: make down

# Stop and remove volumes (destroys PostgreSQL data)
docker compose -f config/docker-compose.yml down -v

# Clean Python caches (PowerShell)
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter .pytest_cache | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter .mypy_cache | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter .ruff_cache | Remove-Item -Recurse -Force
# Or: make clean
```

---

## Setting Environment Variables Persistently

Instead of setting variables each session, you can set them permanently:

### PowerShell (Current User)

```powershell
[System.Environment]::SetEnvironmentVariable("PUF_DB_PASSWORD", "puf_dev_password", "User")
[System.Environment]::SetEnvironmentVariable("PUF_DBT_PASSWORD", "puf_dbt_password", "User")
```

Restart your terminal for changes to take effect.

### System Environment Variables GUI

1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Go to **Advanced** → **Environment Variables**
3. Under **User variables**, click **New**
4. Add `PUF_DB_PASSWORD` = `puf_dev_password`
5. Add `PUF_DBT_PASSWORD` = `puf_dbt_password`

---

## Port Reference

| Port | Service | Protocol | Notes |
|------|---------|----------|-------|
| 3000 | Frontend (Next.js) | HTTP | Dashboard UI |
| 4200 | Prefect Server | HTTP | Flow monitoring UI |
| 5432 | PostgreSQL (direct) | TCP | Admin access only |
| 6432 | PgBouncer (pooled) | TCP | Application connections |
| 8000 | FastAPI | HTTP | REST API + Swagger docs at `/docs` |

---

## Troubleshooting

### Docker Desktop is not running

Docker commands will fail with `error during connect`. Open Docker Desktop from the Start menu and wait for the engine to start (whale icon in system tray stops animating).

### Docker containers won't start

```powershell
# Check if ports are already in use (PowerShell)
netstat -an | Select-String "5432"
netstat -an | Select-String "8000"

# Or use:
Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# View container logs for errors
docker compose -f config/docker-compose.yml logs postgres
docker compose -f config/docker-compose.yml logs api
```

Common port conflicts on Windows:
- **5432** — another PostgreSQL instance (check Services for `postgresql-x64-*`)
- **8000** — another web server
- **3000** — another Node.js app

### WSL 2 / Hyper-V issues

If Docker Desktop fails to start:
- Ensure **WSL 2** is installed: `wsl --install` (requires restart)
- Ensure **virtualization** is enabled in BIOS (Intel VT-x / AMD-V)
- In Docker Desktop Settings → General, confirm "Use the WSL 2 based engine" is checked

### Migrations fail with authentication error

Alembic reads `PUF_DB_PASSWORD` via `%(PUF_DB_PASSWORD)s` interpolation. Ensure the variable is set:

```powershell
# PowerShell
$env:PUF_DB_PASSWORD = "puf_dev_password"
alembic -c pipelines/alembic/alembic.ini upgrade head
```

```cmd
:: CMD
set PUF_DB_PASSWORD=puf_dev_password
alembic -c pipelines/alembic/alembic.ini upgrade head
```

### PowerShell script execution is disabled

If `.ps1` scripts (like venv activation) fail:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `make` is not recognized

Install Make (see [Prerequisites](#make-on-windows)), or run the underlying command directly — every `make` target in this guide also shows the raw command.

### dbt can't connect

dbt uses a separate role (`puf_dbt`) with its own password:

```powershell
$env:PUF_DBT_PASSWORD = "puf_dbt_password"
cd models
dbt run
```

### API returns empty data

Data must be loaded before the API can serve it:

1. Run migrations: `alembic -c pipelines/alembic/alembic.ini upgrade head`
2. Load reference data: `python -m flows.reference_flow`
3. Load utilization data: `python -m flows.utilization_flow --data-year 2022`

### Frontend shows "Failed to fetch"

Ensure the API is running at port 8000 and CORS allows the frontend origin:

```powershell
curl http://localhost:8000/health
# Or: Invoke-RestMethod http://localhost:8000/health
# Should return status "healthy"
```

### Long path issues on Windows

If you encounter `filename too long` errors (common with `node_modules`):

```powershell
git config --global core.longpaths true
```

### Reset everything and start fresh

```powershell
docker compose -f config/docker-compose.yml down -v   # removes pgdata volume
# Or: make down  (then the -v command above)

make clean   # or manually delete __pycache__ dirs
docker compose -f config/docker-compose.yml up -d
$env:PUF_DB_PASSWORD = "puf_dev_password"
alembic -c pipelines/alembic/alembic.ini upgrade head
```

---

## Makefile Reference

Run `make help` to see all targets. If you don't have `make` installed, use the raw command shown in the third column.

| Make Target | Description | Raw Command |
|-------------|-------------|-------------|
| `make help` | Show all targets | — |
| `make install` | Install production deps | `pip install -e .` |
| `make dev` | Install with dev deps | `pip install -e ".[dev]"` then `pre-commit install` |
| `make up` | Start Docker services | `docker compose -f config/docker-compose.yml up -d` |
| `make down` | Stop Docker services | `docker compose -f config/docker-compose.yml down` |
| `make logs` | Tail Docker logs | `docker compose -f config/docker-compose.yml logs -f` |
| `make migrate` | Run Alembic to head | `alembic -c pipelines/alembic/alembic.ini upgrade head` |
| `make migrate-down` | Rollback one migration | `alembic -c pipelines/alembic/alembic.ini downgrade -1` |
| `make migrate-status` | Show migration status | `alembic -c pipelines/alembic/alembic.ini current` |
| `make test` | Run unit tests | `pytest -m "not integration" -v` |
| `make test-all` | Run all tests | `pytest -v` |
| `make test-cov` | Tests with coverage | `pytest -m "not integration" --cov=pipelines --cov=flows --cov=api --cov-report=term-missing` |
| `make lint` | Run linter | `ruff check .` |
| `make format` | Auto-format code | `ruff format .` then `ruff check --fix .` |
| `make typecheck` | Run type checker | `mypy pipelines/ flows/ api/` |
| `make clean` | Remove caches | See [Stopping and Cleaning Up](#stopping-and-cleaning-up) |
| `make db-shell` | Open psql shell | `docker compose -f config/docker-compose.yml exec postgres psql -U puf_admin -d puf` |
| `make prefect-ui` | Print Prefect URL | `echo http://localhost:4200` |
| `make dbt-run` | Run all dbt models | `cd models && dbt run` |
| `make dbt-test` | Run all dbt tests | `cd models && dbt test` |
