# Login Token Size Fix

## Problem

Users are unable to log in to production with the following error:

```
error: value too long for type character varying(512)
at async AuthService.storeRefreshToken
```

## Root Cause

The refresh JWT tokens contain a payload with:
- `userId` (UUID)
- `email` (string)
- `role` (string)
- `practiceIds` (array of UUIDs)

When a user has access to many practices, the `practiceIds` array makes the JWT token exceed 512 characters. The database columns were defined as `varchar(512)`, which is too small.

### Example Token Size

A JWT token with:
- 1 practice: ~400 characters
- 3 practices: ~500 characters
- 5+ practices: **>512 characters** ❌ (causes error)

## Solution

Migration **0005_unique_constraints_and_token_column_fix.sql** (already created) changes the token columns from `varchar(512)` to `TEXT` (unlimited size):

```sql
ALTER TABLE refresh_tokens ALTER COLUMN token TYPE text;
ALTER TABLE password_reset_tokens ALTER COLUMN token TYPE text;
ALTER TABLE blacklisted_tokens ALTER COLUMN token TYPE text;
```

## Files Changed

### 1. Database Schema (`backend/src/database/schema.ts`)

Changed token columns from `varchar(512)` to `text`:

```typescript
// Before
token: varchar('token', { length: 512 }).notNull().unique(),

// After
token: text('token').notNull().unique(),  // Changed to text to accommodate large JWT tokens
```

### 2. Migration Script

**Existing Migration**: `backend/drizzle/0005_unique_constraints_and_token_column_fix.sql`

This migration already exists but hasn't been applied to production yet.

## Applying the Fix to Production

### Option 1: Using the Migration Script (Recommended)

We've created a safe, interactive script to apply the migration:

```bash
# Set database credentials
export DB_HOST="your-production-db-host"
export DB_NAME="dental_erp_prod"
export DB_USER="postgres"
export DB_PASSWORD="your-password"

# Run the migration script
./scripts/apply-token-migration-production.sh
```

The script will:
1. ✅ Test database connection
2. ✅ Check current column types
3. ✅ Prompt for confirmation
4. ✅ Remind you to backup
5. ✅ Apply migration in a transaction
6. ✅ Verify changes

### Option 2: Manual SQL (Advanced)

If you prefer to run SQL directly:

```bash
# Connect to production database
psql -h your-db-host -U postgres -d dental_erp_prod

# Run migration
BEGIN;

ALTER TABLE refresh_tokens ALTER COLUMN token TYPE TEXT;
ALTER TABLE password_reset_tokens ALTER COLUMN token TYPE TEXT;
ALTER TABLE blacklisted_tokens ALTER COLUMN token TYPE TEXT;

COMMIT;

# Verify
\d refresh_tokens
```

### Option 3: Using Docker (if running in containers)

```bash
# Find the postgres container
docker ps | grep postgres

# Connect and run migration
docker exec -it dentalerp-postgres-1 psql -U postgres -d dental_erp_prod -c "
BEGIN;
ALTER TABLE refresh_tokens ALTER COLUMN token TYPE TEXT;
ALTER TABLE password_reset_tokens ALTER COLUMN token TYPE TEXT;
ALTER TABLE blacklisted_tokens ALTER COLUMN token TYPE TEXT;
COMMIT;
"
```

## Verification

After applying the migration, verify it worked:

```sql
-- Check column types
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('refresh_tokens', 'password_reset_tokens', 'blacklisted_tokens')
  AND column_name = 'token';
```

Expected output:
```
     column_name     | data_type
--------------------+-----------
 token              | text
 token              | text
 token              | text
```

## Testing

After applying the migration:

1. **Test Login Flow**:
   ```bash
   curl -X POST https://dentalerp.agentprovision.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@dentalerp.demo","password":"your-password"}'
   ```

2. **Verify No Errors**: Check backend logs for the success message:
   ```
   info: User logged in: test@dentalerp.demo
   ```

3. **Test with Multiple Practices**: Log in as a user with 5+ practice access to ensure large tokens work.

## Rollback Plan

If something goes wrong, you can rollback:

```sql
BEGIN;

ALTER TABLE refresh_tokens ALTER COLUMN token TYPE varchar(2048);
ALTER TABLE password_reset_tokens ALTER COLUMN token TYPE varchar(2048);
ALTER TABLE blacklisted_tokens ALTER COLUMN token TYPE varchar(2048);

COMMIT;
```

Note: Using `varchar(2048)` instead of going back to `512` to prevent future issues. However, `TEXT` is still the recommended solution.

## Future Prevention

### Alternative Solution: Reduce JWT Payload Size

If token size becomes an issue again in the future, consider:

**Option A: Don't store practiceIds in JWT**
```typescript
// Store only userId and fetch practices on each request
const payload: TokenPayload = {
  userId: user.id,
  email: user.email,
  role: user.role,
  // Remove: practiceIds
};
```

**Option B: Store practice count instead of IDs**
```typescript
const payload = {
  userId: user.id,
  email: user.email,
  role: user.role,
  practiceCount: practiceIds.length,  // Just the count
};
```

However, this requires refactoring the auth middleware to fetch practices on each request.

## Related Files

- Migration: `backend/drizzle/0005_unique_constraints_and_token_column_fix.sql`
- Schema: `backend/src/database/schema.ts` (lines 219-241)
- Auth Service: `backend/src/services/auth.ts` (lines 225-241 - token generation)
- Migration Script: `scripts/apply-token-migration-production.sh`

## Status

- [x] Migration created (0005)
- [x] Schema updated
- [x] Production script created
- [ ] Applied to production database
- [ ] Verified in production

## Deployment Checklist

Before deploying this fix:

1. [ ] Backup production database
2. [ ] Apply migration using script or manual SQL
3. [ ] Verify column types changed to TEXT
4. [ ] Test login with user who has multiple practices
5. [ ] Monitor backend logs for any errors
6. [ ] Update this document with deployment date

## Support

If you encounter issues:

1. Check backend logs: `docker logs dentalerp-backend-1`
2. Check database connection
3. Verify migration was applied: `\d refresh_tokens`
4. Contact DevOps team if rollback is needed

---

**Created**: 2024-10-31
**Status**: Ready to Apply
**Priority**: High (Blocking user logins)
