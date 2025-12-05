# Integration Hub Rollout Checklist

## Summary of Recent Changes (2025-10-25)
- **Snowflake connector** migrated into the integration hub (`backend/src/services/integrationHub/connectors/snowflakeConnector.ts`) with environment fallback and cached connections via `snowflakeService`.
- **Credential storage** implemented using encrypted records in `integration_credentials` table plus REST endpoints (`backend/src/routes/integrations.ts`) for list/get/upsert/delete, restricted to admin/executive roles.
- **Frontend admin tooling** added to `frontend/src/pages/integrations/IntegrationsPage.tsx` with React Query hooks (`frontend/src/hooks/useIntegrations.ts`) and API helpers (`frontend/src/services/api.ts`) enabling per-practice credential management via a modal editor.
- **Documentation** expanded with this rollout guide to coordinate backend, frontend, and ops teams.

## Backend preparation
- Ensure `INTEGRATION_CREDENTIAL_KEY` is set and `npm --prefix backend run build` succeeds.
- Run latest database migrations (`npm --prefix backend run migrate`) so `integration_credentials` table exists.
- Remove legacy Snowflake services once integration hub connector is verified: delete `backend/src/services/snowflake.ts` and `backend/src/services/snowflakeIngestion.ts` after checking for remaining imports.

## Credential management API
- Test `/api/integrations/credentials` endpoints with an admin token:
  - `GET /api/integrations/credentials?practiceId=...`
  - `PUT /api/integrations/credentials/{practiceId}/{integrationType}`
  - `DELETE /api/integrations/credentials/{practiceId}/{integrationType}`
- Confirm encryption-at-rest by inspecting DB rows (payload fields should be ciphertext).
- Validate Snowflake connector fallback by staging a manual ingestion upload with and without stored credentials.

## Frontend updates
- Confirm admin/executive users can see the new credential table on `IntegrationsPage.tsx` and create/update/delete entries.
- Ensure non-admin roles do not render credential management controls.
- Verify JSON validation errors in the modal surface clear messages without breaking the UI.

## QA checklist
- Smoke test manual ingestion flow (`scripts/login-and-test-ingestion.sh`) to confirm files land in the configured Snowflake stage.
- Run targeted backend tests if available (`npm --prefix backend test -- integrationHub`).
- Exercise React Query invalidation by editing a credential and ensuring the table refreshes without reload.
- Document any practice-specific secrets in the secure vault (do not store plain text in version control).

## Release communication
- Notify ops that Snowflake credentials can now be managed per practice through the admin UI.
- Share rollback plan: revert to previous commit and restore legacy Snowflake services if critical issues occur.
- Schedule production rollout during a maintenance window due to ingestion staging dependency.
