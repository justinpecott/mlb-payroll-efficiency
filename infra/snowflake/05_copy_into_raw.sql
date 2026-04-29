-- 05_copy_into_raw.sql
-- Load parquet snapshots from S3 stage into Snowflake RAW tables.
--
-- Prerequisites:
--   1) Storage integration exists       (02_storage_integration.sql)
--   2) Stage + file format exist        (03_stage_and_file_formats.sql)
--   3) RAW tables exist                 (04_raw_tables.sql)
--   4) Parquet files are uploaded to S3 under the expected prefixes (see S3 layout below)
--
-- S3 layout under s3://<BUCKET_NAME>/:
--   payroll/parquet/players.parquet
--   payroll/parquet/summary.parquet
--   payroll/parquet/other_payments.parquet
--   batting/batting.parquet
--   pitching/pitching.parquet

-- -----------------------------------------------------------------------------
-- Session context
-- -----------------------------------------------------------------------------
USE ROLE BASEBALL_ROLE;
USE WAREHOUSE baseball_wh;
USE DATABASE BASEBALL;
USE SCHEMA RAW;

-- Sanity check: confirm active context before loading
SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();

-- Confirm expected files are present in the stage before loading
LIST @BASEBALL.RAW.BASEBALL_STAGE;

-- -----------------------------------------------------------------------------
-- COPY INTO: payroll_players
-- -----------------------------------------------------------------------------
COPY INTO BASEBALL.RAW.PAYROLL_PLAYERS
FROM @BASEBALL.RAW.BASEBALL_STAGE/payroll/parquet/players.parquet
FILE_FORMAT = (TYPE = PARQUET, SNAPPY_COMPRESSION = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT';

-- -----------------------------------------------------------------------------
-- COPY INTO: payroll_summary
-- -----------------------------------------------------------------------------
COPY INTO BASEBALL.RAW.PAYROLL_SUMMARY
FROM @BASEBALL.RAW.BASEBALL_STAGE/payroll/parquet/summary.parquet
FILE_FORMAT = (TYPE = PARQUET, SNAPPY_COMPRESSION = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT';

-- -----------------------------------------------------------------------------
-- COPY INTO: payroll_other_payments
-- -----------------------------------------------------------------------------
COPY INTO BASEBALL.RAW.PAYROLL_OTHER_PAYMENTS
FROM @BASEBALL.RAW.BASEBALL_STAGE/payroll/parquet/other_payments.parquet
FILE_FORMAT = (TYPE = PARQUET, SNAPPY_COMPRESSION = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT';

-- -----------------------------------------------------------------------------
-- COPY INTO: batting
-- -----------------------------------------------------------------------------
COPY INTO BASEBALL.RAW.BATTING
FROM @BASEBALL.RAW.BASEBALL_STAGE/batting/batting.parquet
FILE_FORMAT = (TYPE = PARQUET, SNAPPY_COMPRESSION = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT';

-- -----------------------------------------------------------------------------
-- COPY INTO: pitching
-- -----------------------------------------------------------------------------
COPY INTO BASEBALL.RAW.PITCHING
FROM @BASEBALL.RAW.BASEBALL_STAGE/pitching/pitching.parquet
FILE_FORMAT = (TYPE = PARQUET, SNAPPY_COMPRESSION = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT';

-- -----------------------------------------------------------------------------
-- Post-load row count check
-- -----------------------------------------------------------------------------
SELECT 'PAYROLL_PLAYERS'      AS table_name, COUNT(*) AS row_count FROM BASEBALL.RAW.PAYROLL_PLAYERS
UNION ALL
SELECT 'PAYROLL_SUMMARY',       COUNT(*) FROM BASEBALL.RAW.PAYROLL_SUMMARY
UNION ALL
SELECT 'PAYROLL_OTHER_PAYMENTS',COUNT(*) FROM BASEBALL.RAW.PAYROLL_OTHER_PAYMENTS
UNION ALL
SELECT 'BATTING',               COUNT(*) FROM BASEBALL.RAW.BATTING
UNION ALL
SELECT 'PITCHING',              COUNT(*) FROM BASEBALL.RAW.PITCHING
ORDER BY table_name;

-- -----------------------------------------------------------------------------
-- Recent COPY history (last 24 hours) — repeat per table as needed
-- -----------------------------------------------------------------------------
SELECT
    table_name,
    file_name,
    status,
    rows_parsed,
    rows_loaded,
    error_count,
    first_error_message,
    last_load_time
FROM TABLE(
    INFORMATION_SCHEMA.COPY_HISTORY(
        TABLE_NAME   => 'BASEBALL.RAW.PAYROLL_PLAYERS',
        START_TIME   => DATEADD('hour', -24, CURRENT_TIMESTAMP())
    )
)
ORDER BY last_load_time DESC;
