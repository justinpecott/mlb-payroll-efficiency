-- 02_storage_integration.sql
-- Purpose: Create a Snowflake S3 storage integration for loading parquet from S3.
-- Usage: Replace all <PLACEHOLDER> values before running.

-- ---------------------------------------------------------------------------
-- 0) Run as ACCOUNTADMIN (required for CREATE INTEGRATION privilege)
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- 1) Create (or replace) the storage integration
-- ---------------------------------------------------------------------------
CREATE OR REPLACE STORAGE INTEGRATION s3_baseball_analytics_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<AWS_IAM_ROLE_ARN>'
  STORAGE_ALLOWED_LOCATIONS = (
    's3://<BUCKET_NAME>/'
  );

-- ---------------------------------------------------------------------------
-- 2) Inspect integration details
--    Copy the following output values and update the AWS IAM trust policy:
--      - STORAGE_AWS_IAM_USER_ARN  → goes into "Principal.AWS" in the trust policy
--      - STORAGE_AWS_EXTERNAL_ID   → goes into "Condition.StringEquals.sts:ExternalId"
--    See: infra/aws/aws_setup.md for the full trust policy update procedure.
-- ---------------------------------------------------------------------------
DESC INTEGRATION s3_baseball_analytics_integration;

-- ---------------------------------------------------------------------------
-- 3) Grant usage to the project role (least privilege)
-- ---------------------------------------------------------------------------
GRANT USAGE ON INTEGRATION s3_baseball_analytics_integration TO ROLE BASEBALL_ROLE;

-- ---------------------------------------------------------------------------
-- 4) Verify
-- ---------------------------------------------------------------------------
SHOW INTEGRATIONS LIKE 's3_baseball_analytics_integration';

-- Notes:
-- - STORAGE_ALLOWED_LOCATIONS is scoped to this bucket only.
-- - No secrets are hardcoded; authentication uses IAM role assumption.
-- - Next step: create file format + external stage (03_stage_and_file_formats.sql).
