-- 01_context.sql
-- Purpose: Establish a consistent Snowflake session context before running raw-load scripts.
-- Usage: Run this after 00_initial_setup.sql, then execute 02_*.sql, 03_*.sql, etc.

-- -----------------------------------------------------------------------------
-- 1) Configure environment-specific values
-- -----------------------------------------------------------------------------
SET sf_role      = 'BASEBALL_ROLE';
SET sf_warehouse = 'BASEBALL_WH';
SET sf_database  = 'BASEBALL';
SET sf_schema    = 'RAW';

-- Optional metadata for observability
SET sf_query_tag = 'baseball_analytics_raw_load';

-- -----------------------------------------------------------------------------
-- 2) Apply session context
-- -----------------------------------------------------------------------------
USE ROLE IDENTIFIER($sf_role);
USE WAREHOUSE IDENTIFIER($sf_warehouse);
USE DATABASE IDENTIFIER($sf_database);
USE SCHEMA IDENTIFIER($sf_schema);

ALTER SESSION SET QUERY_TAG = $sf_query_tag;
ALTER SESSION SET TIMEZONE = 'UTC';

-- -----------------------------------------------------------------------------
-- 3) Confirm active context (sanity check)
-- -----------------------------------------------------------------------------
SELECT
  CURRENT_ROLE()      AS active_role,
  CURRENT_WAREHOUSE() AS active_warehouse,
  CURRENT_DATABASE()  AS active_database,
  CURRENT_SCHEMA()    AS active_schema,
  CURRENT_REGION()    AS active_region,
  CURRENT_ACCOUNT()   AS active_account;

-- -----------------------------------------------------------------------------
-- Optional: uncomment if you want this script to create missing containers.
-- Keep commented by default to avoid accidental object creation in wrong env.
-- -----------------------------------------------------------------------------
-- CREATE DATABASE IF NOT EXISTS IDENTIFIER($sf_database);
-- CREATE SCHEMA IF NOT EXISTS IDENTIFIER($sf_database || '.' || $sf_schema);
