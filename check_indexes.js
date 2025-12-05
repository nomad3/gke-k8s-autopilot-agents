const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

async function main() {
    const client = await pool.connect();
    try {
        const res = await client.query(`
      SELECT indexname, indexdef
      FROM pg_indexes
      WHERE tablename = 'refresh_tokens';
    `);
        console.log('Indexes on refresh_tokens:', res.rows);
    } catch (e) {
        console.error('Query failed', e);
    } finally {
        client.release();
        await pool.end();
    }
}
main();
