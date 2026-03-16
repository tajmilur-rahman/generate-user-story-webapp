-- ============================================================================
-- Database Migration Script for User Story Automation
-- ============================================================================
-- This file contains SQL migrations for the PostgreSQL database.
-- New changes should be appended to the end of this file.
--
-- Usage:
--   psql -U user -d database < scripts/dbmigration.sql
--
-- ============================================================================

-- ============================================================================
-- INITIAL SCHEMA (for new installations)
-- ============================================================================
-- This creates the users table if it doesn't exist
-- Safe to run on existing databases (will skip if table exists)

CREATE TABLE IF NOT EXISTS users (
	id SERIAL PRIMARY KEY,
	google_id VARCHAR(255) NOT NULL UNIQUE,
	email VARCHAR(255) NOT NULL UNIQUE,
	name VARCHAR(255),
	picture VARCHAR(500),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	github_username VARCHAR(255),
	github_access_token VARCHAR(500),
	github_repo VARCHAR(255),
	github_branch VARCHAR(255),
	github_folder VARCHAR(255)
);

-- ============================================================================
-- MIGRATION 1: Add GitHub Integration Fields (2026-03-11)
-- ============================================================================
-- These ALTER TABLE statements add GitHub fields to existing users table
-- Uses DO block to handle cases where columns already exist

DO $$
BEGIN
    -- Add github_username column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='users' AND column_name='github_username') THEN
        ALTER TABLE users ADD COLUMN github_username VARCHAR(255);
    END IF;

    -- Add github_access_token column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='users' AND column_name='github_access_token') THEN
        ALTER TABLE users ADD COLUMN github_access_token VARCHAR(500);
    END IF;

    -- Add github_repo column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='users' AND column_name='github_repo') THEN
        ALTER TABLE users ADD COLUMN github_repo VARCHAR(255);
    END IF;

    -- Add github_branch column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='users' AND column_name='github_branch') THEN
        ALTER TABLE users ADD COLUMN github_branch VARCHAR(255);
    END IF;

    -- Add github_folder column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='users' AND column_name='github_folder') THEN
        ALTER TABLE users ADD COLUMN github_folder VARCHAR(255);
    END IF;
END $$;

-- ============================================================================
-- END OF MIGRATIONS
-- ============================================================================
-- Future migrations should be added below this line
-- Always include:
--   - Date of migration
--   - Description of changes
--   - SQL statements wrapped in DO blocks for idempotency
-- ============================================================================
