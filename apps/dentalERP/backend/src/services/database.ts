import { drizzle } from 'drizzle-orm/node-postgres';
import { eq } from 'drizzle-orm';
import { Pool } from 'pg';
import * as schema from '../database/schema';
import { logger } from '../utils/logger';
import { ensureCoreTables } from '../database/ensure';

export class DatabaseService {
  private static instance: DatabaseService;
  private pool: Pool | null = null;
  private db: any = null;

  private constructor() {}

  public static getInstance(): DatabaseService {
    if (!DatabaseService.instance) {
      DatabaseService.instance = new DatabaseService();
    }
    return DatabaseService.instance;
  }

  async initialize(): Promise<void> {
    try {
      this.pool = new Pool({
        connectionString: process.env.DATABASE_URL,
        max: 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
      });

      this.db = drizzle(this.pool, { schema });

      // Test connection
      await this.pool.query('SELECT NOW()');
      logger.info('Database connected successfully');

      // Lightweight ensure of core tables/columns for resilience
      await ensureCoreTables(this.pool);
      logger.info('Core database tables ensured');
    } catch (error) {
      logger.error('Database connection failed:', error);
      throw error;
    }
  }

  async checkHealth(): Promise<boolean> {
    try {
      if (!this.pool) return false;
      const result = await this.pool.query('SELECT 1');
      return result.rows.length > 0;
    } catch (error) {
      logger.error('Database health check failed:', error);
      return false;
    }
  }

  async close(): Promise<void> {
    if (this.pool) {
      await this.pool.end();
      this.pool = null;
      this.db = null;
    }
  }

  getDb() {
    if (!this.db) {
      throw new Error('Database not initialized');
    }
    return this.db;
  }

  // User methods (placeholder implementations)
  async createUser(userData: any): Promise<any> {
    logger.info('Creating user:', userData.email);
    const [inserted] = await this.db
      .insert(schema.users)
      .values(userData)
      .returning();
    return inserted;
  }

  async findUserByEmail(email: string): Promise<any> {
    logger.info('Finding user by email:', email);
    const rows = await this.db
      .select()
      .from(schema.users)
      .where(eq(schema.users.email, email))
      .limit(1);
    return rows[0] ?? null;
  }

  async findUserById(id: string): Promise<any> {
    logger.info('Finding user by ID:', id);
    const rows = await this.db
      .select()
      .from(schema.users)
      .where(eq(schema.users.id, id))
      .limit(1);
    return rows[0] ?? null;
  }

  async updateUserLastLogin(userId: string): Promise<void> {
    logger.info('Updating last login for user:', userId);
    await this.db
      .update(schema.users)
      .set({ lastLogin: new Date(), updatedAt: new Date() })
      .where(eq(schema.users.id, userId));
  }

  async updateUserPassword(userId: string, passwordHash: string): Promise<void> {
    logger.info('Updating password for user:', userId);
    await this.db
      .update(schema.users)
      .set({ passwordHash, updatedAt: new Date() })
      .where(eq(schema.users.id, userId));
  }

  async getUserPractices(userId: string): Promise<any[]> {
    logger.info('Getting user practices for:', userId);
    const rows = await this.db
      .select()
      .from(schema.userPractices)
      .where(eq(schema.userPractices.userId, userId));
    return rows;
  }
}
