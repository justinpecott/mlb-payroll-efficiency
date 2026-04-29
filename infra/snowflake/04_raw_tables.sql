-- 04_raw_tables.sql
-- Purpose: Create RAW-layer tables from parquet schema metadata in S3.
--
-- Prereqs:
--   - Storage integration + stage exists (see 02/03 scripts)
--   - Parquet files are uploaded under the expected prefixes
--   - File format FF_PARQUET exists (defined in 03_stage_and_file_formats.sql)
--
-- Notes:
--   - Uses INFER_SCHEMA so you don't need to hand-maintain 500+ stat columns.
--   - CREATE OR REPLACE is intentional for repeatable rebuilds in this one-off project.

USE ROLE BASEBALL_ROLE;
USE WAREHOUSE baseball_wh;
USE DATABASE BASEBALL;
USE SCHEMA RAW;

-- Adjust these if your stage path conventions differ.
SET STAGE_PATH = '@BASEBALL.RAW.BASEBALL_STAGE';
SET FILE_FORMAT_NAME = 'BASEBALL.RAW.FF_PARQUET';

-- ------------------------------------------------------------
-- Payroll tables
-- ------------------------------------------------------------

CREATE OR REPLACE TABLE payroll_players
USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
    FROM TABLE(
        INFER_SCHEMA(
            LOCATION => $STAGE_PATH || '/payroll/parquet/players.parquet',
            FILE_FORMAT => $FILE_FORMAT_NAME
        )
    )
);

CREATE OR REPLACE TABLE payroll_summary
USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
    FROM TABLE(
        INFER_SCHEMA(
            LOCATION => $STAGE_PATH || '/payroll/parquet/summary.parquet',
            FILE_FORMAT => $FILE_FORMAT_NAME
        )
    )
);

CREATE OR REPLACE TABLE payroll_other_payments
USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
    FROM TABLE(
        INFER_SCHEMA(
            LOCATION => $STAGE_PATH || '/payroll/parquet/other_payments.parquet',
            FILE_FORMAT => $FILE_FORMAT_NAME
        )
    )
);

-- ------------------------------------------------------------
-- Player stats tables
-- ------------------------------------------------------------

CREATE OR REPLACE TABLE batting
USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
    FROM TABLE(
        INFER_SCHEMA(
            LOCATION => $STAGE_PATH || '/batting/batting.parquet',
            FILE_FORMAT => $FILE_FORMAT_NAME
        )
    )
);

CREATE OR REPLACE TABLE pitching
USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
    FROM TABLE(
        INFER_SCHEMA(
            LOCATION => $STAGE_PATH || '/pitching/pitching.parquet',
            FILE_FORMAT => $FILE_FORMAT_NAME
        )
    )
);

-- Optional sanity checks
SHOW TABLES LIKE 'PAYROLL_%' IN SCHEMA BASEBALL.RAW;
SHOW TABLES LIKE 'BATTING' IN SCHEMA BASEBALL.RAW;
SHOW TABLES LIKE 'PITCHING' IN SCHEMA BASEBALL.RAW;
