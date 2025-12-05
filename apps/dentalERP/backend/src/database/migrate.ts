import 'dotenv/config';
import { Pool } from 'pg';

async function main() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // Extensions
    await client.query(`CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`);
    await client.query(`CREATE EXTENSION IF NOT EXISTS pgcrypto;`);

    // Users table
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        email varchar(255) UNIQUE NOT NULL,
        password_hash varchar(255) NOT NULL,
        role varchar(20) NOT NULL,
        first_name varchar(100),
        last_name varchar(100),
        avatar text,
        phone varchar(20),
        preferences jsonb NOT NULL DEFAULT '{}'::jsonb,
        active boolean NOT NULL DEFAULT true,
        last_login timestamptz,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );
      CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
      ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name varchar(100);
      ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name varchar(100);
      ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar text;
      ALTER TABLE users ADD COLUMN IF NOT EXISTS phone varchar(20);
      ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences jsonb NOT NULL DEFAULT '{}'::jsonb;
      ALTER TABLE users ADD COLUMN IF NOT EXISTS active boolean DEFAULT true;
      ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login timestamptz;
    `);

    // Practices table
    await client.query(`
      CREATE TABLE IF NOT EXISTS practices (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name varchar(255) NOT NULL,
        description text,
        address jsonb NOT NULL DEFAULT '{}'::jsonb,
        phone varchar(20),
        email varchar(255),
        operating_hours jsonb,
        website varchar(255),
        tax_id varchar(50),
        settings jsonb NOT NULL DEFAULT '{}'::jsonb,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );
      ALTER TABLE practices
        ADD COLUMN IF NOT EXISTS description text,
        ADD COLUMN IF NOT EXISTS address jsonb NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS phone varchar(20),
        ADD COLUMN IF NOT EXISTS email varchar(255),
        ADD COLUMN IF NOT EXISTS operating_hours jsonb,
        ADD COLUMN IF NOT EXISTS website varchar(255),
        ADD COLUMN IF NOT EXISTS tax_id varchar(50),
        ADD COLUMN IF NOT EXISTS settings jsonb NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true,
        ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
        ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
    `);

    // Locations table (for multi-location practices)
    await client.query(`
      CREATE TABLE IF NOT EXISTS locations (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        practice_id uuid NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        name varchar(255) NOT NULL,
        address jsonb NOT NULL DEFAULT '{}'::jsonb,
        phone varchar(20),
        email varchar(255),
        operating_hours jsonb,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );
      ALTER TABLE locations
        ADD COLUMN IF NOT EXISTS address jsonb NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS phone varchar(20),
        ADD COLUMN IF NOT EXISTS email varchar(255),
        ADD COLUMN IF NOT EXISTS operating_hours jsonb,
        ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true,
        ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
        ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
    `);

    // User-Practices junction table
    await client.query(`
      CREATE TABLE IF NOT EXISTS user_practices (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        practice_id uuid NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        role varchar(20) NOT NULL,
        permissions jsonb NOT NULL DEFAULT '[]'::jsonb,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_user_practice UNIQUE(user_id, practice_id)
      );
    `);

    // Integration credentials table
    await client.query(`
      CREATE TABLE IF NOT EXISTS integration_credentials (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        practice_id uuid NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        integration_type varchar(100) NOT NULL,
        name varchar(255) NOT NULL,
        credentials jsonb NOT NULL,
        metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_by uuid REFERENCES users(id) ON DELETE SET NULL,
        updated_by uuid REFERENCES users(id) ON DELETE SET NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );

      CREATE UNIQUE INDEX IF NOT EXISTS integration_credentials_practice_type_unique
        ON integration_credentials (practice_id, integration_type);

      CREATE INDEX IF NOT EXISTS integration_credentials_practice_idx
        ON integration_credentials (practice_id);
    `);

    // Patients table
    await client.query(`
      CREATE TABLE IF NOT EXISTS patients (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        practice_id uuid NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        first_name varchar(100) NOT NULL,
        last_name varchar(100) NOT NULL,
        email varchar(255),
        phone varchar(20),
        status varchar(20) NOT NULL DEFAULT 'active',
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );
      ALTER TABLE patients
        ADD COLUMN IF NOT EXISTS external_id varchar(100),
        ADD COLUMN IF NOT EXISTS date_of_birth timestamptz,
        ADD COLUMN IF NOT EXISTS gender varchar(20),
        ADD COLUMN IF NOT EXISTS address jsonb,
        ADD COLUMN IF NOT EXISTS emergency_contact jsonb,
        ADD COLUMN IF NOT EXISTS insurance jsonb NOT NULL DEFAULT '[]'::jsonb,
        ADD COLUMN IF NOT EXISTS medical_history jsonb NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS dental_history jsonb NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS notes text,
        ADD COLUMN IF NOT EXISTS last_visit timestamptz,
        ADD COLUMN IF NOT EXISTS next_appointment timestamptz;
    `);

    // Appointments table
    await client.query(`
      CREATE TABLE IF NOT EXISTS appointments (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        practice_id uuid NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        patient_id uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        provider_id uuid NOT NULL REFERENCES users(id),
        location_id uuid REFERENCES locations(id),
        scheduled_start timestamptz NOT NULL,
        scheduled_end timestamptz NOT NULL,
        appointment_type varchar(100),
        procedures jsonb NOT NULL DEFAULT '[]'::jsonb,
        status varchar(30) NOT NULL DEFAULT 'scheduled',
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );
      ALTER TABLE appointments
        ADD COLUMN IF NOT EXISTS external_id varchar(100),
        ADD COLUMN IF NOT EXISTS actual_start timestamptz,
        ADD COLUMN IF NOT EXISTS actual_end timestamptz,
        ADD COLUMN IF NOT EXISTS check_in_time timestamptz,
        ADD COLUMN IF NOT EXISTS wait_time integer,
        ADD COLUMN IF NOT EXISTS room_number varchar(20),
        ADD COLUMN IF NOT EXISTS notes text;
    `);

    // Integrations table
    await client.query(`
      CREATE TABLE IF NOT EXISTS integrations (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        practice_id uuid NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        type varchar(50) NOT NULL,
        name varchar(255) NOT NULL,
        status varchar(30) NOT NULL DEFAULT 'pending',
        config jsonb NOT NULL,
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );
      ALTER TABLE integrations
        ADD COLUMN IF NOT EXISTS last_sync timestamptz,
        ADD COLUMN IF NOT EXISTS last_error text;
    `);

    // Auth-related tables
    await client.query(`
      CREATE TABLE IF NOT EXISTS refresh_tokens (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token text NOT NULL UNIQUE,
        token_hash varchar(32),
        expires_at timestamptz NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );

      CREATE INDEX IF NOT EXISTS refresh_tokens_user_idx ON refresh_tokens(user_id);
      CREATE UNIQUE INDEX IF NOT EXISTS refresh_tokens_token_hash_idx ON refresh_tokens(token_hash);

      ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS token_hash varchar(32);
      CREATE UNIQUE INDEX IF NOT EXISTS refresh_tokens_token_hash_idx ON refresh_tokens(token_hash);

      ALTER TABLE refresh_tokens ALTER COLUMN token TYPE text;
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token varchar(512) NOT NULL UNIQUE,
        expires_at timestamptz NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
      );

      CREATE INDEX IF NOT EXISTS password_reset_tokens_user_idx ON password_reset_tokens(user_id);
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS blacklisted_tokens (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        token varchar(512) NOT NULL UNIQUE,
        expires_at timestamptz NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
      );
    `);

    // BI Daily Metrics table for aggregated analytics
    await client.query(`
      CREATE TABLE IF NOT EXISTS bi_daily_metrics (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        practice_id uuid NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        location_id uuid REFERENCES locations(id),
        date timestamptz NOT NULL,
        revenue integer DEFAULT 0,
        target_revenue integer DEFAULT 0,
        new_patients integer DEFAULT 0,
        returning_patients integer DEFAULT 0,
        schedule_utilization integer DEFAULT 0,
        no_shows integer DEFAULT 0,
        cancellations integer DEFAULT 0,
        avg_wait_time integer DEFAULT 0,
        staff_utilization integer DEFAULT 0,
        chair_utilization integer DEFAULT 0,
        ontime_performance integer DEFAULT 0,
        treatment_completion integer DEFAULT 0,
        claims_submitted integer DEFAULT 0,
        claims_denied integer DEFAULT 0,
        collections_amount integer DEFAULT 0,
        ar_current integer DEFAULT 0,
        ar_30 integer DEFAULT 0,
        ar_60 integer DEFAULT 0,
        ar_90 integer DEFAULT 0,
        benchmark_score integer DEFAULT 0,
        forecast_revenue integer DEFAULT 0,
        forecast_patients integer DEFAULT 0,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );
      ALTER TABLE bi_daily_metrics
        ADD COLUMN IF NOT EXISTS location_id uuid REFERENCES locations(id),
        ADD COLUMN IF NOT EXISTS revenue integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS target_revenue integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS new_patients integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS returning_patients integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS schedule_utilization integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS no_shows integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS cancellations integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS avg_wait_time integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS staff_utilization integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS chair_utilization integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS ontime_performance integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS treatment_completion integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS claims_submitted integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS claims_denied integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS collections_amount integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS ar_current integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS ar_30 integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS ar_60 integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS ar_90 integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS benchmark_score integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS forecast_revenue integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS forecast_patients integer DEFAULT 0,
        ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
        ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
    `);

    // Manual ingestion uploads table
    await client.query(`
      CREATE TABLE IF NOT EXISTS manual_ingestion_uploads (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        practice_id uuid NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
        uploaded_by uuid REFERENCES users(id) ON DELETE SET NULL,
        source_system varchar(100) NOT NULL,
        dataset varchar(100) NOT NULL DEFAULT 'unknown',
        original_filename varchar(512) NOT NULL,
        storage_path varchar(1024) NOT NULL,
        status varchar(50) NOT NULL DEFAULT 'stored',
        external_location varchar(1024),
        notes text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      );

      CREATE INDEX IF NOT EXISTS manual_ingestion_uploads_practice_idx ON manual_ingestion_uploads(practice_id);
      CREATE INDEX IF NOT EXISTS manual_ingestion_uploads_status_idx ON manual_ingestion_uploads(status);
      CREATE INDEX IF NOT EXISTS manual_ingestion_uploads_created_at_idx ON manual_ingestion_uploads(created_at);
    `);

    await client.query('COMMIT');
    console.log('✅ Migration completed successfully');
  } catch (e) {
    await client.query('ROLLBACK');
    console.error('❌ Migration failed', e);
    process.exit(1);
  } finally {
    client.release();
    await pool.end();
  }
}

main();
