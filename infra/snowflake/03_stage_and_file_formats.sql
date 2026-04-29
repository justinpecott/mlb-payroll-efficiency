-- 03_stage_and_file_formats.sql
-- -----------------------------------------------------------------------------
-- Purpose:
--   Create Snowflake Parquet file format and external stage objects used for
--   S3 → RAW loads.
--
-- Notes:
--   1) Update object names/URLs to match your account conventions.
--   2) Assumes storage integration already exists (see 02_storage_integration.sql).
-- -----------------------------------------------------------------------------

-- Session context (adjust as needed)
USE ROLE BASEBALL_ROLE;
USE WAREHOUSE baseball_wh;
USE DATABASE BASEBALL;
USE SCHEMA RAW;

-- -----------------------------------------------------------------------------
-- File formats
-- -----------------------------------------------------------------------------

-- Canonical format for this project's archived snapshots in data/parquet/
-- (kept as a named file format for use with INFER_SCHEMA in 04_raw_tables.sql)
CREATE FILE FORMAT IF NOT EXISTS FF_PARQUET
  TYPE = PARQUET
  COMPRESSION = AUTO
  BINARY_AS_TEXT = FALSE
  COMMENT = 'Parquet format for baseball analytics raw loads';

-- -----------------------------------------------------------------------------
-- External stage
-- -----------------------------------------------------------------------------
-- Replace URL and integration names if yours differ.

CREATE STAGE IF NOT EXISTS BASEBALL_STAGE
  URL = 's3://<BUCKET_NAME>/'
  STORAGE_INTEGRATION = s3_baseball_analytics_integration
  FILE_FORMAT = FF_PARQUET
  COMMENT = 'Primary S3 stage for baseball analytics raw loads';

-- Optional: enable stage directory table metadata
ALTER STAGE BASEBALL_STAGE SET DIRECTORY = (ENABLE = TRUE);

-- -----------------------------------------------------------------------------
-- Validation / smoke checks
-- -----------------------------------------------------------------------------

DESC STAGE BASEBALL_STAGE;
SHOW FILE FORMATS LIKE 'FF_PARQUET' IN SCHEMA BASEBALL.RAW;
LIST @BASEBALL_STAGE;
