import { and, desc, eq, inArray } from 'drizzle-orm';
import { manualIngestionUploads } from '../database/schema';
import { DatabaseService } from './database';

export type ManualIngestionStatus = 'stored' | 'delivered' | 'failed' | 'archived';

type CreateUploadParams = {
  practiceId: string;
  uploadedBy?: string;
  sourceSystem: string;
  dataset?: string;
  originalFilename: string;
  storagePath: string;
  status?: ManualIngestionStatus;
  externalLocation?: string | null;
  notes?: string | null;
};

type UpdateUploadParams = {
  status?: ManualIngestionStatus;
  externalLocation?: string | null;
  notes?: string | null;
};

type ListUploadsOptions = {
  practiceIds?: string[];
  limit?: number;
  statuses?: ManualIngestionStatus[];
};

export class ManualIngestionService {
  static async createUpload(params: CreateUploadParams) {
    const db = DatabaseService.getInstance().getDb();
    const [upload] = await db
      .insert(manualIngestionUploads)
      .values({
        practiceId: params.practiceId,
        uploadedBy: params.uploadedBy ?? null,
        sourceSystem: params.sourceSystem,
        dataset: params.dataset ?? 'unknown',
        originalFilename: params.originalFilename,
        storagePath: params.storagePath,
        status: params.status ?? 'stored',
        externalLocation: params.externalLocation ?? null,
        notes: params.notes ?? null,
        createdAt: new Date(),
        updatedAt: new Date(),
      })
      .returning();

    return upload;
  }

  static async listUploads(options: ListUploadsOptions = {}) {
    const db = DatabaseService.getInstance().getDb();
    const limit = options.limit && Number.isFinite(options.limit)
      ? Math.min(Math.max(options.limit, 1), 200)
      : 100;

    const conditions = [] as ReturnType<typeof eq>[];

    if (options.practiceIds && options.practiceIds.length) {
      conditions.push(inArray(manualIngestionUploads.practiceId, options.practiceIds));
    }

    if (options.statuses && options.statuses.length) {
      conditions.push(inArray(manualIngestionUploads.status, options.statuses));
    }

    let query = db
      .select()
      .from(manualIngestionUploads)
      .orderBy(desc(manualIngestionUploads.createdAt))
      .limit(limit);

    if (conditions.length === 1) {
      query = query.where(conditions[0]);
    } else if (conditions.length > 1) {
      query = query.where(and(...conditions));
    }

    return query;
  }

  static async getUpload(id: string) {
    const db = DatabaseService.getInstance().getDb();
    const [upload] = await db
      .select()
      .from(manualIngestionUploads)
      .where(eq(manualIngestionUploads.id, id))
      .limit(1);

    return upload ?? null;
  }

  static async updateUpload(id: string, params: UpdateUploadParams) {
    const db = DatabaseService.getInstance().getDb();
    const updates: Record<string, unknown> = {
      updatedAt: new Date(),
    };

    if (params.status !== undefined) updates.status = params.status;
    if (params.externalLocation !== undefined) updates.externalLocation = params.externalLocation;
    if (params.notes !== undefined) updates.notes = params.notes;

    const [upload] = await db
      .update(manualIngestionUploads)
      .set(updates)
      .where(eq(manualIngestionUploads.id, id))
      .returning();

    return upload ?? null;
  }

  static async deleteUpload(id: string) {
    const db = DatabaseService.getInstance().getDb();
    const upload = await this.getUpload(id);
    if (!upload) {
      return null;
    }

    await db.delete(manualIngestionUploads).where(eq(manualIngestionUploads.id, id));
    return upload;
  }
}
