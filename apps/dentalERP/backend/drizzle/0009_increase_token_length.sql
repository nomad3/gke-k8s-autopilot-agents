-- Increase token column lengths to accommodate longer JWT tokens
ALTER TABLE "refresh_tokens" ALTER COLUMN "token" TYPE varchar(1024);
ALTER TABLE "refresh_tokens" ALTER COLUMN "token_hash" TYPE varchar(1024);
