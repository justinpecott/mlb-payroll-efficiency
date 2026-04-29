# Snowflake RAW Load Guide (Execution Order)

This folder is for **infrastructure SQL** used to set up and load the Snowflake RAW layer from S3.  
Keep these scripts separate from dbt models so ingestion setup is explicit, repeatable, and auditable.

---

## Purpose

These scripts establish:

1. Initial Snowflake bootstrap (database, schemas, warehouse, role, grants)
2. Snowflake execution context (role, warehouse, database, schema)
3. Storage integration and external stage
4. File format(s) for parquet ingestion
5. RAW table definitions
6. `COPY INTO` load steps from S3 into `BASEBALL.RAW`
7. Validation checks after load

---

## Recommended Script Order

Run scripts in this order:

1. `00_initial_setup.sql`
2. `01_context.sql`
3. `02_storage_integration.sql`
4. `03_stage_and_file_formats.sql`
5. `04_raw_tables.sql`
6. `05_copy_into_raw.sql`
7. `06_validation_queries.sql`

If you split by object type further (roles, grants, pipes, tasks), keep a numeric prefix and preserve deterministic ordering.

---

## Project Conventions

Use the project defaults unless you intentionally override them:

- **Database:** `BASEBALL`
- **Schema:** `RAW`
- **Role:** `BASEBALL_ROLE`
- **Warehouse:** `baseball_wh`
- **Storage Integration:** `s3_baseball_analytics_integration`
- **Stage:** `BASEBALL.RAW.BASEBALL_STAGE`

---

## Operational Notes

- Treat `data/parquet/` snapshots as canonical for this project.
- Prefer idempotent SQL (`CREATE ... IF NOT EXISTS` where possible).
- Avoid destructive commands in shared environments unless explicitly needed.
- Keep load scripts environment-safe (no hardcoded secrets).
- If credentials or IAM trust change, re-validate integration and stage access first.

---

## Example Contents by Script

### `00_initial_setup.sql`

Create baseline Snowflake objects and access controls for the project:

- Database: `BASEBALL`
- Schemas: `RAW`, `ANALYTICS`, `ANALYTICS_DEV`
- Warehouse: `BASEBALL_WH`
- Role: `BASEBALL_ROLE`
- Grants for current and future schema/object usage
- Grant role to a placeholder user (replace with real username before execution)

### `01_context.sql`

Set role/warehouse/database/schema for consistent execution context.

### `02_storage_integration.sql`

Create or verify storage integration and required grants/trust setup.

### `03_stage_and_file_formats.sql`

Create parquet file format and external stage pointing to the S3 location.

### `04_raw_tables.sql`

Create RAW tables aligned to parquet schema (or generated DDL artifacts).

### `05_copy_into_raw.sql`

Load each dataset into matching RAW tables with `COPY INTO`.

Typical table set:

- `payroll_players`
- `payroll_summary`
- `payroll_other_payments`
- `batting`
- `pitching`

### `06_validation_queries.sql`

Row counts, null checks on key columns, season/team sanity checks, and spot checks.

---

## Suggested Validation Checklist

After `COPY INTO`:

- Confirm row counts are non-zero for expected tables.
- Confirm expected season range (2021–2025).
- Confirm key identifiers exist (`player_id`, `team`, `season` as applicable).
- Compare sample counts against parquet-side expectations.
- Save validation output in `docs/runbooks/` if you want a reproducible audit trail.

---

## How This Connects to dbt

Once RAW is loaded and validated:

1. Run dbt staging models (`transform/dbt/models/staging/`)
2. Run dbt marts (`transform/dbt/models/marts/`)
3. Run dbt tests

Example commands after the dbt project move:

- `dbt deps --project-dir transform/dbt`
- `dbt run --project-dir transform/dbt --select staging.*`
- `dbt run --project-dir transform/dbt --select marts.*`
- `dbt test --project-dir transform/dbt`

This folder handles ingestion setup/loading only; transformation logic stays in dbt.

---

## Security Reminder

Do **not** store secrets in these SQL files.  
Use Snowflake-native integrations/roles and environment-managed credentials.
