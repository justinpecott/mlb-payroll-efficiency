-- 06_validation_queries.sql
-- Post-load validation checks for RAW layer tables.
-- Run after COPY INTO scripts complete.
--
-- Assumptions:
--   - Database: BASEBALL
--   - Schema: RAW
--   - Seasons in scope: 2021-2025

USE ROLE BASEBALL_ROLE;
USE WAREHOUSE baseball_wh;
USE DATABASE BASEBALL;
USE SCHEMA RAW;

-- ----------------------------------------------------------------------
-- 1) High-level row counts
-- ----------------------------------------------------------------------
SELECT 'payroll_players' AS table_name, COUNT(*) AS row_count FROM payroll_players
UNION ALL
SELECT 'payroll_summary' AS table_name, COUNT(*) AS row_count FROM payroll_summary
UNION ALL
SELECT 'payroll_other_payments' AS table_name, COUNT(*) AS row_count FROM payroll_other_payments
UNION ALL
SELECT 'batting' AS table_name, COUNT(*) AS row_count FROM batting
UNION ALL
SELECT 'pitching' AS table_name, COUNT(*) AS row_count FROM pitching
ORDER BY table_name;

-- ----------------------------------------------------------------------
-- 2) Season coverage (expect 2021-2025)
-- ----------------------------------------------------------------------
SELECT
    'payroll_players' AS table_name,
    MIN(season) AS min_season,
    MAX(season) AS max_season,
    COUNT(DISTINCT season) AS distinct_seasons
FROM payroll_players
UNION ALL
SELECT
    'payroll_summary' AS table_name,
    MIN(season) AS min_season,
    MAX(season) AS max_season,
    COUNT(DISTINCT season) AS distinct_seasons
FROM payroll_summary
UNION ALL
SELECT
    'payroll_other_payments' AS table_name,
    MIN(season) AS min_season,
    MAX(season) AS max_season,
    COUNT(DISTINCT season) AS distinct_seasons
FROM payroll_other_payments
UNION ALL
SELECT
    'batting' AS table_name,
    MIN(season) AS min_season,
    MAX(season) AS max_season,
    COUNT(DISTINCT season) AS distinct_seasons
FROM batting
UNION ALL
SELECT
    'pitching' AS table_name,
    MIN(season) AS min_season,
    MAX(season) AS max_season,
    COUNT(DISTINCT season) AS distinct_seasons
FROM pitching
ORDER BY table_name;

-- ----------------------------------------------------------------------
-- 3) Team-season coverage checks for payroll tables
-- ----------------------------------------------------------------------
-- Expect ~30 teams per season in payroll_summary.
SELECT
    season,
    COUNT(DISTINCT team) AS teams_in_summary
FROM payroll_summary
GROUP BY season
ORDER BY season;

-- Compare distinct team-season combos between payroll players and summary.
WITH players_team_season AS (
    SELECT DISTINCT team, season FROM payroll_players
),
summary_team_season AS (
    SELECT DISTINCT team, season FROM payroll_summary
)
SELECT
    COALESCE(p.team, s.team) AS team,
    COALESCE(p.season, s.season) AS season,
    CASE WHEN p.team IS NULL THEN 'missing_in_payroll_players'
         WHEN s.team IS NULL THEN 'missing_in_payroll_summary'
         ELSE 'present_in_both'
    END AS status
FROM players_team_season p
FULL OUTER JOIN summary_team_season s
    ON p.team = s.team
   AND p.season = s.season
WHERE p.team IS NULL OR s.team IS NULL
ORDER BY season, team;

-- ----------------------------------------------------------------------
-- 4) Null / blank key field checks
-- ----------------------------------------------------------------------
SELECT
    COUNT_IF(player_id IS NULL OR TRIM(player_id) = '') AS null_or_blank_player_id,
    COUNT_IF(player IS NULL OR TRIM(player) = '') AS null_or_blank_player_name,
    COUNT_IF(team IS NULL OR TRIM(team) = '') AS null_or_blank_team,
    COUNT_IF(season IS NULL) AS null_season,
    COUNT_IF(salary IS NULL) AS null_salary
FROM payroll_players;

SELECT
    COUNT_IF(team IS NULL OR TRIM(team) = '') AS null_or_blank_team,
    COUNT_IF(season IS NULL) AS null_season,
    COUNT_IF(luxury_tax_payroll_estimate IS NULL) AS null_luxury_tax_payroll_estimate
FROM payroll_summary;

SELECT
    COUNT_IF(description IS NULL OR TRIM(description) = '') AS null_or_blank_description,
    COUNT_IF(team IS NULL OR TRIM(team) = '') AS null_or_blank_team,
    COUNT_IF(season IS NULL) AS null_season
FROM payroll_other_payments;

-- ----------------------------------------------------------------------
-- 5) Duplicate row checks on expected natural keys
-- ----------------------------------------------------------------------
-- payroll_players: duplicates on player/team/season/contract_status may indicate bad load.
SELECT
    player_id,
    team,
    season,
    contract_status,
    COUNT(*) AS duplicate_count
FROM payroll_players
GROUP BY player_id, team, season, contract_status
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, season, team, player_id;

-- payroll_summary: one row per team-season expected.
SELECT
    team,
    season,
    COUNT(*) AS duplicate_count
FROM payroll_summary
GROUP BY team, season
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, season, team;

-- ----------------------------------------------------------------------
-- 6) Data quality spot checks for payroll numbers
-- ----------------------------------------------------------------------
-- Negative salaries are generally unexpected for payroll players.
SELECT
    COUNT(*) AS negative_salary_rows
FROM payroll_players
WHERE salary < 0;

-- Extremely high salaries (sanity check threshold can be tuned).
SELECT
    player,
    team,
    season,
    salary
FROM payroll_players
WHERE salary > 60000000
ORDER BY salary DESC;

-- ----------------------------------------------------------------------
-- 7) International-player ID marker presence (sa-prefixed IDs)
-- ----------------------------------------------------------------------
-- These are expected to appear in raw and be filtered in staging.
SELECT
    season,
    COUNT(*) AS sa_prefixed_players
FROM payroll_players
WHERE LOWER(player_id) LIKE 'sa%'
GROUP BY season
ORDER BY season;

-- ----------------------------------------------------------------------
-- 8) Raw stats table sanity checks
-- ----------------------------------------------------------------------
SELECT
    season,
    COUNT(*) AS batting_rows
FROM batting
GROUP BY season
ORDER BY season;

SELECT
    season,
    COUNT(*) AS pitching_rows
FROM pitching
GROUP BY season
ORDER BY season;

-- ----------------------------------------------------------------------
-- 9) Source file lineage checks (payroll parquet provenance)
-- ----------------------------------------------------------------------
SELECT
    source_file,
    COUNT(*) AS rows_loaded
FROM payroll_players
GROUP BY source_file
ORDER BY rows_loaded DESC, source_file;

SELECT
    source_file,
    COUNT(*) AS rows_loaded
FROM payroll_summary
GROUP BY source_file
ORDER BY rows_loaded DESC, source_file;

SELECT
    source_file,
    COUNT(*) AS rows_loaded
FROM payroll_other_payments
GROUP BY source_file
ORDER BY rows_loaded DESC, source_file;

-- ----------------------------------------------------------------------
-- 10) Optional: COPY history snapshot (last 24 hours)
-- ----------------------------------------------------------------------
-- Useful for auditing whether expected files were loaded and whether errors occurred.
SELECT
    table_name,
    file_name,
    last_load_time,
    status,
    row_count,
    row_parsed,
    errors_seen,
    first_error_message
FROM TABLE(
    INFORMATION_SCHEMA.COPY_HISTORY(
        TABLE_NAME => 'BASEBALL.RAW.PAYROLL_PLAYERS',
        START_TIME => DATEADD('hour', -24, CURRENT_TIMESTAMP())
    )
)
ORDER BY last_load_time DESC;

SELECT
    table_name,
    file_name,
    last_load_time,
    status,
    row_count,
    row_parsed,
    errors_seen,
    first_error_message
FROM TABLE(
    INFORMATION_SCHEMA.COPY_HISTORY(
        TABLE_NAME => 'BASEBALL.RAW.PAYROLL_SUMMARY',
        START_TIME => DATEADD('hour', -24, CURRENT_TIMESTAMP())
    )
)
ORDER BY last_load_time DESC;

SELECT
    table_name,
    file_name,
    last_load_time,
    status,
    row_count,
    row_parsed,
    errors_seen,
    first_error_message
FROM TABLE(
    INFORMATION_SCHEMA.COPY_HISTORY(
        TABLE_NAME => 'BASEBALL.RAW.PAYROLL_OTHER_PAYMENTS',
        START_TIME => DATEADD('hour', -24, CURRENT_TIMESTAMP())
    )
)
ORDER BY last_load_time DESC;

SELECT
    table_name,
    file_name,
    last_load_time,
    status,
    row_count,
    row_parsed,
    errors_seen,
    first_error_message
FROM TABLE(
    INFORMATION_SCHEMA.COPY_HISTORY(
        TABLE_NAME => 'BASEBALL.RAW.BATTING',
        START_TIME => DATEADD('hour', -24, CURRENT_TIMESTAMP())
    )
)
ORDER BY last_load_time DESC;

SELECT
    table_name,
    file_name,
    last_load_time,
    status,
    row_count,
    row_parsed,
    errors_seen,
    first_error_message
FROM TABLE(
    INFORMATION_SCHEMA.COPY_HISTORY(
        TABLE_NAME => 'BASEBALL.RAW.PITCHING',
        START_TIME => DATEADD('hour', -24, CURRENT_TIMESTAMP())
    )
)
ORDER BY last_load_time DESC;
