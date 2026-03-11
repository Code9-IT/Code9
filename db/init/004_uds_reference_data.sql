-- =============================================================
-- Maritime Observability - Scope 1 UDS reference data
-- =============================================================
-- Seeds the minimal owner / vessel / application reference data
-- needed for:
--   - Del B UDS seeding
--   - Del C UDS MCP queries
--   - Del D UDS Grafana dashboard
--
-- This is a tracked adaptation of Geir's init script so the Scope 1
-- prototype works from a fresh database without relying on local-only files.
-- =============================================================

BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -------------------------------------------------------------
-- Owners
-- -------------------------------------------------------------
INSERT INTO owners (id, name)
VALUES
  ('11111111-1111-1111-1111-111111111111'::uuid, 'Oceanic Shipping AS'),
  ('22222222-2222-2222-2222-222222222222'::uuid, 'Nordic Tankers ASA')
ON CONFLICT (name) DO NOTHING;

-- -------------------------------------------------------------
-- Vessels / UDS locations
-- -------------------------------------------------------------
INSERT INTO udslocations (
  id,
  external_id,
  name,
  imo_nr,
  owner_id,
  owner_from,
  created_at,
  updated_at
)
VALUES
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1'::uuid,
    'SHIP-EXT-001',
    'MV Egde Aurora',
    'IMO9300001',
    '11111111-1111-1111-1111-111111111111'::uuid,
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  ),
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2'::uuid,
    'SHIP-EXT-002',
    'MV Egde Borealis',
    'IMO9300002',
    '11111111-1111-1111-1111-111111111111'::uuid,
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  ),
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3'::uuid,
    'SHIP-EXT-003',
    'MT Nordic Fjord',
    'IMO9300003',
    '22222222-2222-2222-2222-222222222222'::uuid,
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  )
ON CONFLICT (imo_nr) DO NOTHING;

-- -------------------------------------------------------------
-- Applications
-- -------------------------------------------------------------
INSERT INTO applications (id, external_id, name, app_type, created_at, updated_at)
VALUES
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1'::uuid,
    'time-series-processor',
    'Time Series Processor',
    'service',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2'::uuid,
    'data-quality-processor',
    'Data Quality Processor',
    'service',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb3'::uuid,
    'uds-topic-handler-edge',
    'Topic Handler Edge',
    'service',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb4'::uuid,
    'uds-edge-data-api',
    'Data Api Edge',
    'service',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb5'::uuid,
    'uds-edge-ingest-source-admin',
    'Ingest Source Admin',
    'service',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb6'::uuid,
    'uds-edge-parquet-sync',
    'Parquet Sync',
    'job',
    timezone('UTC', now()) - interval '180 days',
    timezone('UTC', now())
  )
ON CONFLICT (external_id) DO NOTHING;

-- -------------------------------------------------------------
-- Location/application links
-- -------------------------------------------------------------
INSERT INTO uds_location_application_instances (uds_location_id, application_instance_id)
SELECT u.id, a.id
FROM udslocations u
JOIN applications a ON true
WHERE u.imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
  AND a.external_id IN (
    'time-series-processor',
    'data-quality-processor',
    'uds-topic-handler-edge',
    'uds-edge-data-api',
    'uds-edge-ingest-source-admin',
    'uds-edge-parquet-sync'
  )
ON CONFLICT DO NOTHING;

-- -------------------------------------------------------------
-- Ownership history
-- -------------------------------------------------------------
INSERT INTO uds_location_owner_history (
  id,
  uds_location_id,
  owner_id,
  owner_from,
  owner_to,
  created_at
)
SELECT
  gen_random_uuid(),
  u.id,
  u.owner_id,
  u.owner_from,
  NULL,
  timezone('UTC', now())
FROM udslocations u
WHERE u.imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
  AND u.owner_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM uds_location_owner_history h
    WHERE h.uds_location_id = u.id
      AND h.owner_id = u.owner_id
      AND h.owner_from = u.owner_from
  );

-- -------------------------------------------------------------
-- Monitoring configs compatibility shim
-- -------------------------------------------------------------
INSERT INTO monitoring_configs (
  id,
  imo_number,
  monitoring_config_json,
  created_at,
  updated_at,
  updated_by
)
SELECT
  gen_random_uuid(),
  u.imo_nr,
  jsonb_build_object(
    'imo', u.imo_nr,
    'ship_name', u.name,
    'query_enabled', true,
    'query_interval_minutes', 30
  ),
  timezone('UTC', now()) - interval '30 days',
  timezone('UTC', now()),
  'seed'
FROM udslocations u
WHERE u.imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
ON CONFLICT (imo_number) DO NOTHING;

COMMIT;
