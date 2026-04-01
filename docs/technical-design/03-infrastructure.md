# 3. Infrastructure & Deployment

[← Back to Index](index.md) | [← System Architecture](02-system-architecture.md)

---

## Deployment Topology

```d2
direction: right

docker: Docker Compose Network {
  style.fill: "#f0f9ff"
  style.stroke: "#0ea5e9"

  postgres: "PostgreSQL 16\n:5432" {shape: cylinder; style.fill: "#dbeafe"}
  pgbouncer: "PgBouncer\n:6432" {shape: diamond; style.fill: "#e0e7ff"}
  prefect_server: "Prefect Server\n:4200" {shape: rectangle; style.fill: "#fef3c7"}
  prefect_worker: "Prefect Worker\n(process pool)" {shape: rectangle; style.fill: "#fef9c3"}
  api: "FastAPI\n:8000" {shape: rectangle; style.fill: "#dcfce7"}
  frontend: "Next.js\n:3000" {shape: rectangle; style.fill: "#f3e8ff"}

  pgbouncer -> postgres: "healthy"
  prefect_server -> postgres: "healthy"
  prefect_worker -> prefect_server: "healthy"
  api -> postgres: "healthy"
  frontend -> api: "healthy"
}

external: "External\nAccess" {shape: cloud; style.fill: "#fecaca"}
external -> docker.frontend: ":3000"
external -> docker.api: ":8000"
external -> docker.prefect_server: ":4200"
external -> docker.pgbouncer: ":6432"
```

Full diagram: [`diagrams/deployment-topology.d2`](diagrams/deployment-topology.d2)

---

## Docker Compose Services

Source: `config/docker-compose.yml`

| Service | Image | Port | Depends On | Health Check |
|---------|-------|------|------------|-------------|
| postgres | `postgres:16-alpine` | 5432 | — | `pg_isready` every 5s |
| pgbouncer | `bitnami/pgbouncer:latest` | 6432 | postgres (healthy) | `pg_isready` on 6432 every 10s |
| prefect-server | `prefecthq/prefect:3-latest` | 4200 | postgres (healthy) | HTTP `/api/health` every 15s |
| prefect-worker | `prefecthq/prefect:3-latest` | — | prefect-server (healthy) | — |
| api | Custom (`config/Dockerfile.api`) | 8000 | postgres (healthy) | HTTP `/health` every 10s |
| frontend | Custom (`frontend/Dockerfile`) | 3000 | api (healthy) | — |

Named volume: `pgdata` (local driver).

---

## PostgreSQL Tuning

Applied via `postgres` command overrides in `docker-compose.yml`:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `shared_buffers` | 512MB | Working set cache |
| `effective_cache_size` | 1GB | Query planner hint for total available cache |
| `work_mem` | 64MB | Per-sort/hash memory |
| `maintenance_work_mem` | 256MB | VACUUM, CREATE INDEX budget |
| `max_connections` | 200 | Total connection slots |
| `wal_buffers` | 16MB | WAL write buffer |
| `random_page_cost` | 1.1 | SSD-optimized (default 4.0) |
| `effective_io_concurrency` | 200 | SSD parallel I/O |
| `max_wal_size` | 2GB | Checkpoint spacing |
| `checkpoint_completion_target` | 0.9 | Spread checkpoint I/O |
| `shm_size` | 256MB | Shared memory for PG |

---

## PgBouncer Configuration

| Parameter | Value |
|-----------|-------|
| Pool mode | `transaction` |
| Max client connections | 200 |
| Default pool size | 20 |
| Min pool size | 5 |

---

## Port Mapping

| Port | Service | Protocol |
|------|---------|----------|
| 3000 | Frontend (Next.js) | HTTP |
| 4200 | Prefect UI | HTTP |
| 5432 | PostgreSQL (direct) | TCP |
| 6432 | PgBouncer (pooled) | TCP |
| 8000 | FastAPI | HTTP |

---

## Makefile Targets

Source: `Makefile` (20 targets)

| Target | Description |
|--------|-------------|
| `help` | Show all targets with descriptions |
| `install` | Install production dependencies |
| `dev` | Install with dev dependencies + pre-commit hooks |
| `up` | Start all Docker services |
| `down` | Stop all Docker services |
| `logs` | Tail Docker service logs |
| `migrate` | Run Alembic migrations to head |
| `migrate-down` | Rollback last Alembic migration |
| `migrate-status` | Show current migration status |
| `test` | Run tests (excluding integration) |
| `test-all` | Run all tests including integration |
| `test-cov` | Run tests with coverage report |
| `lint` | Run Ruff linter |
| `format` | Format code with Ruff |
| `typecheck` | Run mypy type checker |
| `clean` | Remove build artifacts and caches |
| `db-shell` | Open psql shell to PostgreSQL |
| `prefect-ui` | Print Prefect UI URL |
| `dbt-run` | Run all dbt models |
| `dbt-test` | Run all dbt tests |

---

## Environment Variables

| Variable | Default | Used By |
|----------|---------|---------|
| `PUF_DB_HOST` | `localhost` | Pipelines, API |
| `PUF_DB_PORT` | `5432` | Pipelines, API |
| `PUF_DB_NAME` | `puf` | Pipelines, API |
| `PUF_DB_USER` | (role-specific) | API: `puf_api` |
| `PUF_DB_PASSWORD` | `puf_dev_password` | All services |
| `PUF_PGBOUNCER_PORT` | `6432` | Application connections |
| `PREFECT_API_URL` | `http://prefect-server:4200/api` | Prefect worker |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Frontend |

---

**Next:** [Database →](04-database.md)
