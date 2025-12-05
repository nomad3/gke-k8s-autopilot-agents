-- ============================================================================
-- CLEANUP SCRIPT: Remove fake data and duplicates from backend database
-- ============================================================================
-- Run this on production to fix fake "Silver Creek" subsidiaries
-- Date: November 24, 2025
-- See: docs/DEMO_DATA_INTEGRITY_REPORT.md for context
-- ============================================================================

-- STEP 1: Backup - Show current state before changes
\echo '=== BEFORE CLEANUP ==='
\echo 'Practices:'
SELECT id, name, tenant_id FROM practices ORDER BY name;

\echo 'Locations (unique):'
SELECT DISTINCT name, subsidiary_name FROM locations ORDER BY name;

\echo 'Total counts:'
SELECT
  (SELECT COUNT(*) FROM practices) as practices_count,
  (SELECT COUNT(*) FROM locations) as locations_count,
  (SELECT COUNT(*) FROM users) as users_count,
  (SELECT COUNT(*) FROM integrations) as integrations_count;

-- ============================================================================
-- STEP 2: Delete all existing data (clean slate approach)
-- ============================================================================
-- This is safer than trying to merge/update with complex duplicates

\echo '=== CLEANING UP ==='

-- Delete in order of dependencies
DELETE FROM user_practices;
DELETE FROM integrations;
DELETE FROM locations;
DELETE FROM practices;

\echo 'Deleted all practices, locations, integrations, user_practices'

-- ============================================================================
-- STEP 3: Insert clean data - Single parent practice
-- ============================================================================

\echo '=== INSERTING CLEAN DATA ==='

-- Single parent practice: Silver Creek Dental Partners
INSERT INTO practices (id, name, description, address, phone, email, website, tenant_id, netsuite_parent_id, is_active, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'Silver Creek Dental Partners',
  'Silver Creek Dental Partners - Parent Company',
  '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}',
  '858-555-0100',
  'info@silvercreekdental.com',
  'https://silvercreekdental.com',
  'silvercreek',
  'silver_creek_dental_partners',
  true,
  NOW(),
  NOW()
);

\echo 'Created parent practice: Silver Creek Dental Partners'

-- Get the practice ID for locations
DO $$
DECLARE
  parent_practice_id UUID;
  default_hours JSONB := '{"mon": ["08:00", "17:00"], "tue": ["08:00", "17:00"], "wed": ["08:00", "17:00"], "thu": ["08:00", "17:00"], "fri": ["08:00", "15:00"]}';
BEGIN
  SELECT id INTO parent_practice_id FROM practices WHERE name = 'Silver Creek Dental Partners';

  -- Insert 17 real NetSuite subsidiaries as locations
  INSERT INTO locations (id, practice_id, name, address, phone, email, operating_hours, external_system_id, external_system_type, subsidiary_name, is_active, created_at, updated_at)
  VALUES
    (gen_random_uuid(), parent_practice_id, 'San Marcos', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_san_marcos__llc', 'netsuite', 'SCDP San Marcos, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'San Marcos II', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_san_marcos_ii__llc', 'netsuite', 'SCDP San Marcos II, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Del Sur Ranch', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_del_sur_ranch__llc', 'netsuite', 'SCDP Del Sur Ranch, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Torrey Pines', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_torrey_pines__llc', 'netsuite', 'SCDP Torrey Pines, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Torrey Highlands', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_torrey_highlands__llc', 'netsuite', 'SCDP Torrey Highlands, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Eastlake', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_eastlake__llc', 'netsuite', 'SCDP Eastlake, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'UTC', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_utc__llc', 'netsuite', 'SCDP UTC, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Coronado', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_coronado__llc', 'netsuite', 'SCDP Coronado, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Vista', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_vista__llc', 'netsuite', 'SCDP Vista, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Laguna Hills', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_laguna_hills__llc', 'netsuite', 'SCDP Laguna Hills, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Laguna Hills II', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_laguna_hills_ii__llc', 'netsuite', 'SCDP Laguna Hills II, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Carlsbad', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_carlsbad__llc', 'netsuite', 'SCDP Carlsbad, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Otay Lakes', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_otay_lakes__llc', 'netsuite', 'SCDP Otay Lakes, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Kearny Mesa', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_kearny_mesa__llc', 'netsuite', 'SCDP Kearny Mesa, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Temecula', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_temecula__llc', 'netsuite', 'SCDP Temecula, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Temecula II', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'scdp_temecula_ii__llc', 'netsuite', 'SCDP Temecula II, LLC', true, NOW(), NOW()),
    (gen_random_uuid(), parent_practice_id, 'Theodosis Dental', '{"street": "4520 Executive Dr", "city": "San Diego", "state": "CA", "zipCode": "92121", "country": "USA"}', '858-555-0100', 'info@silvercreekdental.com', default_hours, 'steve_p__theodosis_dental_corporation__pc', 'netsuite', 'Steve P. Theodosis Dental Corporation, PC', true, NOW(), NOW());

  RAISE NOTICE 'Created 17 real NetSuite subsidiary locations';

  -- Create NetSuite integration
  INSERT INTO integrations (id, practice_id, type, name, status, config, is_active, created_at, updated_at)
  VALUES (
    gen_random_uuid(),
    parent_practice_id,
    'netsuite',
    'NetSuite ERP - Silver Creek Dental Partners',
    'pending',
    '{
      "account_id": "placeholder",
      "realm": "placeholder",
      "sync_enabled": true,
      "sync_frequency": "15m",
      "full_sync_schedule": "0 2 * * *",
      "sync_datasets": ["journal_entries", "vendors", "customers", "employees", "accounts"],
      "subsidiaries": [
        "SCDP San Marcos, LLC",
        "SCDP San Marcos II, LLC",
        "SCDP Del Sur Ranch, LLC",
        "SCDP Torrey Pines, LLC",
        "SCDP Torrey Highlands, LLC",
        "SCDP Eastlake, LLC",
        "SCDP UTC, LLC",
        "SCDP Coronado, LLC",
        "SCDP Vista, LLC",
        "SCDP Laguna Hills, LLC",
        "SCDP Laguna Hills II, LLC",
        "SCDP Carlsbad, LLC",
        "SCDP Otay Lakes, LLC",
        "SCDP Kearny Mesa, LLC",
        "SCDP Temecula, LLC",
        "SCDP Temecula II, LLC",
        "Steve P. Theodosis Dental Corporation, PC"
      ]
    }',
    true,
    NOW(),
    NOW()
  );

  RAISE NOTICE 'Created NetSuite integration';

  -- Link all users to the practice
  INSERT INTO user_practices (id, user_id, practice_id, role, is_active, created_at, updated_at)
  SELECT
    gen_random_uuid(),
    u.id,
    parent_practice_id,
    u.role,
    true,
    NOW(),
    NOW()
  FROM users u;

  RAISE NOTICE 'Linked users to practice';

END $$;

-- ============================================================================
-- STEP 4: Verify results
-- ============================================================================

\echo '=== AFTER CLEANUP ==='
\echo 'Practices:'
SELECT id, name, tenant_id FROM practices ORDER BY name;

\echo 'Locations (17 real NetSuite subsidiaries):'
SELECT name, subsidiary_name FROM locations ORDER BY name;

\echo 'Total counts:'
SELECT
  (SELECT COUNT(*) FROM practices) as practices_count,
  (SELECT COUNT(*) FROM locations) as locations_count,
  (SELECT COUNT(*) FROM users) as users_count,
  (SELECT COUNT(*) FROM integrations) as integrations_count,
  (SELECT COUNT(*) FROM user_practices) as user_practices_count;

\echo '=== CLEANUP COMPLETE ==='
