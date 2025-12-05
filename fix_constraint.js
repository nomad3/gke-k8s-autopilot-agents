const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

async function main() {
    const client = await pool.connect();
    try {
        await client.query('BEGIN');
        console.log('Dropping index refresh_tokens_token_hash_idx...');
        await client.query('DROP INDEX IF EXISTS refresh_tokens_token_hash_idx;');
        console.log('Adding unique constraint refresh_tokens_token_hash_key...');
        await client.query('ALTER TABLE refresh_tokens ADD CONSTRAINT refresh_tokens_token_hash_key UNIQUE (token_hash);');
        await client.query('COMMIT');
        console.log('Constraint added successfully.');
    } catch (e) {
        await client.query('ROLLBACK');
        console.error('Constraint addition failed', e);
        process.exit(1);
    } finally {
        client.release();
        await pool.end();
    }
}
main();
