import type { Config } from 'drizzle-kit';

// Prefer DATABASE_URL, then DRIZZLE_DATABASE_URL, then sensible local default
const connectionString =
  process.env.DATABASE_URL ||
  process.env.DRIZZLE_DATABASE_URL ||
  'postgresql://postgres:postgres@localhost:5432/dental_erp_dev';

export default {
  schema: ['./src/database/schema.ts', './src/database/ingestion.ts'],
  out: './drizzle',
  driver: 'pg',
  dbCredentials: {
    connectionString,
  },
} satisfies Config;
