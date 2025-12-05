-- Cleanup existing NetSuite duplicate records
-- Keeps most recent record (by extracted_at), deletes older duplicates

-- Journal Entries
DELETE FROM bronze.netsuite_journal_entries
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_journal_entries
    GROUP BY id
);

-- Accounts
DELETE FROM bronze.netsuite_accounts
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_accounts
    GROUP BY id
);

-- Vendor Bills
DELETE FROM bronze.netsuite_vendor_bills
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_vendor_bills
    GROUP BY id
);

-- Customers
DELETE FROM bronze.netsuite_customers
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_customers
    GROUP BY id
);

-- Vendors
DELETE FROM bronze.netsuite_vendors
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_vendors
    GROUP BY id
);

-- Subsidiaries
DELETE FROM bronze.netsuite_subsidiaries
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_subsidiaries
    GROUP BY id
);

-- Verify cleanup
SELECT 'netsuite_journal_entries' as table_name, COUNT(*) as total, COUNT(DISTINCT id) as distinct_ids FROM bronze.netsuite_journal_entries
UNION ALL
SELECT 'netsuite_accounts', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_accounts
UNION ALL
SELECT 'netsuite_vendor_bills', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_vendor_bills
UNION ALL
SELECT 'netsuite_customers', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_customers
UNION ALL
SELECT 'netsuite_vendors', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_vendors
UNION ALL
SELECT 'netsuite_subsidiaries', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_subsidiaries;
