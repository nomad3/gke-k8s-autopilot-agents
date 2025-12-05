-- Add NetSuite fields to practices table
ALTER TABLE "practices" ADD COLUMN IF NOT EXISTS "tenant_id" varchar(50);
ALTER TABLE "practices" ADD COLUMN IF NOT EXISTS "netsuite_parent_id" varchar(100);

-- Create index for tenant_id
CREATE INDEX IF NOT EXISTS "practices_tenant_id_idx" ON "practices" ("tenant_id");

-- Add NetSuite fields to locations table
ALTER TABLE "locations" ADD COLUMN IF NOT EXISTS "external_system_id" varchar(100);
ALTER TABLE "locations" ADD COLUMN IF NOT EXISTS "external_system_type" varchar(50);
ALTER TABLE "locations" ADD COLUMN IF NOT EXISTS "subsidiary_name" varchar(255);

-- Create index for external system
CREATE INDEX IF NOT EXISTS "locations_external_system_idx" ON "locations" ("external_system_id", "external_system_type");
