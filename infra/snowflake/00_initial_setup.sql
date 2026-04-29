-- 00_initial_setup.sql
-- Purpose: Bootstrap core Snowflake objects for this project:
--   - Database
--   - Schemas (RAW, ANALYTICS, ANALYTICS_DEV)
--   - Warehouse
--   - Role
--   - Grants (current + future access patterns)
--   - Role assignment to a placeholder user
--
-- Run as ACCOUNTADMIN for initial bootstrap.

USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- 1) Configure names / defaults
-- ---------------------------------------------------------------------------
SET sf_database      = 'BASEBALL';
SET sf_schema_raw    = 'RAW';
SET sf_schema_analytics = 'ANALYTICS';
SET sf_schema_analytics_dev = 'ANALYTICS_DEV';

SET sf_warehouse     = 'BASEBALL_WH';
SET sf_role          = 'BASEBALL_ROLE';

-- Replace with your actual Snowflake username before running:
SET sf_placeholder_user = 'YOUR_SNOWFLAKE_USERNAME';

-- Warehouse settings
SET sf_wh_size       = 'XSMALL';
SET sf_wh_suspend_s  = 60;
SET sf_wh_resume     = TRUE;

-- ---------------------------------------------------------------------------
-- 2) Create role, warehouse, database, schemas
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS IDENTIFIER($sf_role);

CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER($sf_warehouse)
  WAREHOUSE_SIZE = $sf_wh_size
  AUTO_SUSPEND = $sf_wh_suspend_s
  AUTO_RESUME = $sf_wh_resume
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for baseball analytics project';

CREATE DATABASE IF NOT EXISTS IDENTIFIER($sf_database)
  COMMENT = 'Database for baseball payroll efficiency analytics';

CREATE SCHEMA IF NOT EXISTS IDENTIFIER($sf_database || '.' || $sf_schema_raw);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($sf_database || '.' || $sf_schema_analytics);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev);

-- ---------------------------------------------------------------------------
-- 3) Core role grants
-- ---------------------------------------------------------------------------

-- Warehouse access
GRANT USAGE, OPERATE ON WAREHOUSE IDENTIFIER($sf_warehouse) TO ROLE IDENTIFIER($sf_role);

-- Database and schema usage
GRANT USAGE ON DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);
GRANT USAGE ON ALL SCHEMAS IN DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);

-- Read access across all current/future relational objects in database
GRANT SELECT ON ALL TABLES IN DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE TABLES IN DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);

GRANT SELECT ON ALL VIEWS IN DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE VIEWS IN DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);

GRANT SELECT ON ALL MATERIALIZED VIEWS IN DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE MATERIALIZED VIEWS IN DATABASE IDENTIFIER($sf_database) TO ROLE IDENTIFIER($sf_role);

-- ---------------------------------------------------------------------------
-- 4) Schema-specific build/load privileges
-- ---------------------------------------------------------------------------

-- RAW: supports ingestion objects + table loads
GRANT USAGE ON SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_raw) TO ROLE IDENTIFIER($sf_role);
GRANT CREATE TABLE, CREATE VIEW, CREATE STAGE, CREATE FILE FORMAT
  ON SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_raw)
  TO ROLE IDENTIFIER($sf_role);

GRANT INSERT, UPDATE, DELETE, TRUNCATE
  ON ALL TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_raw)
  TO ROLE IDENTIFIER($sf_role);

GRANT INSERT, UPDATE, DELETE, TRUNCATE
  ON FUTURE TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_raw)
  TO ROLE IDENTIFIER($sf_role);

-- ANALYTICS: production transformation outputs
GRANT USAGE ON SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics) TO ROLE IDENTIFIER($sf_role);
GRANT CREATE TABLE, CREATE VIEW
  ON SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics)
  TO ROLE IDENTIFIER($sf_role);

GRANT SELECT ON ALL TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics) TO ROLE IDENTIFIER($sf_role);

GRANT SELECT ON ALL VIEWS IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE VIEWS IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics) TO ROLE IDENTIFIER($sf_role);

GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE MATERIALIZED VIEWS IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics) TO ROLE IDENTIFIER($sf_role);

GRANT INSERT, UPDATE, DELETE, TRUNCATE
  ON ALL TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics)
  TO ROLE IDENTIFIER($sf_role);

GRANT INSERT, UPDATE, DELETE, TRUNCATE
  ON FUTURE TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics)
  TO ROLE IDENTIFIER($sf_role);

-- ANALYTICS_DEV: development/scratch transformation outputs
GRANT USAGE ON SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev) TO ROLE IDENTIFIER($sf_role);
GRANT CREATE TABLE, CREATE VIEW
  ON SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev)
  TO ROLE IDENTIFIER($sf_role);

GRANT SELECT ON ALL TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev) TO ROLE IDENTIFIER($sf_role);

GRANT SELECT ON ALL VIEWS IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE VIEWS IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev) TO ROLE IDENTIFIER($sf_role);

GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev) TO ROLE IDENTIFIER($sf_role);
GRANT SELECT ON FUTURE MATERIALIZED VIEWS IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev) TO ROLE IDENTIFIER($sf_role);

GRANT INSERT, UPDATE, DELETE, TRUNCATE
  ON ALL TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev)
  TO ROLE IDENTIFIER($sf_role);

GRANT INSERT, UPDATE, DELETE, TRUNCATE
  ON FUTURE TABLES IN SCHEMA IDENTIFIER($sf_database || '.' || $sf_schema_analytics_dev)
  TO ROLE IDENTIFIER($sf_role);

-- ---------------------------------------------------------------------------
-- 5) Grant role to placeholder user
-- ---------------------------------------------------------------------------
GRANT ROLE IDENTIFIER($sf_role) TO USER IDENTIFIER($sf_placeholder_user);

-- ---------------------------------------------------------------------------
-- 6) Optional sanity checks
-- ---------------------------------------------------------------------------
SHOW DATABASES LIKE $sf_database;
SHOW SCHEMAS IN DATABASE IDENTIFIER($sf_database);
SHOW WAREHOUSES LIKE $sf_warehouse;
SHOW ROLES LIKE $sf_role;
SHOW GRANTS TO ROLE IDENTIFIER($sf_role);
SHOW GRANTS TO USER IDENTIFIER($sf_placeholder_user);
