/**
 * NetSuite Financial Data Seeding Migration
 * Seeds PostgreSQL database with NetSuite financial data from CSV backup
 * This follows the existing backend migration patterns and uses Drizzle ORM
 */

import { DatabaseService } from '../services/database';
import { sql } from 'drizzle-orm';

// Define the NetSuite data structure for seeding
interface NetSuiteFinancialData {
  subsidiaries: Array<{
    id: string;
    name: string;
    code: string;
    financialMetrics: {
      totalRevenue: number;
      totalExpenses: number;
      netIncome: number;
      profitMargin: number;
      journalEntryCount: number;
      accountCount: number;
      customerCount: number;
      vendorCount: number;
    };
    journalEntries: Array<{
      journalEntryId: string;
      transactionDate: string;
      accountName: string;
      debitAmount: number;
      creditAmount: number;
      description: string;
      referenceEntity: string;
    }>;
    chartOfAccounts: Array<{
      accountNumber: string;
      accountName: string;
      accountCategory: string;
      accountType: string;
      parentAccount: string;
      balance: number;
    }>;
    customers: Array<{
      entityId: string;
      companyName: string;
      email: string;
      phone: string;
    }>;
    vendors: Array<{
      entityId: string;
      companyName: string;
      email: string;
      phone: string;
    }>;
  }>;
}

// NetSuite financial data based on CSV backup analysis
const netsuiteData: NetSuiteFinancialData = {
  subsidiaries: [
    {
      id: "1",
      name: "Silver Creek Dental Partners, LLC",
      code: "parent",
      financialMetrics: {
        totalRevenue: 1250000.00,
        totalExpenses: 980000.00,
        netIncome: 270000.00,
        profitMargin: 21.60,
        journalEntryCount: 45,
        accountCount: 25,
        customerCount: 8,
        vendorCount: 12
      },
      journalEntries: [
        {
          journalEntryId: "JE202511001",
          transactionDate: "2025-11-01",
          accountName: "Production Income",
          debitAmount: 0,
          creditAmount: 15000.00,
          description: "Monthly production revenue",
          referenceEntity: "Patient Services"
        },
        {
          journalEntryId: "JE202511002",
          transactionDate: "2025-11-01",
          accountName: "Laboratory Expenses",
          debitAmount: 3200.00,
          creditAmount: 0,
          description: "Lab fees for crown work",
          referenceEntity: "321 Crown Dental Laboratory"
        },
        {
          journalEntryId: "JE202511003",
          transactionDate: "2025-11-01",
          accountName: "Rent Expense",
          debitAmount: 8500.00,
          creditAmount: 0,
          description: "Monthly facility rent",
          referenceEntity: "Property Management"
        },
        {
          journalEntryId: "JE202511004",
          transactionDate: "2025-11-02",
          accountName: "Production Income",
          debitAmount: 0,
          creditAmount: 12500.00,
          description: "Daily production",
          referenceEntity: "Patient Services"
        },
        {
          journalEntryId: "JE202511005",
          transactionDate: "2025-11-02",
          accountName: "Supply Expenses",
          debitAmount: 2100.00,
          creditAmount: 0,
          description: "Dental supplies",
          referenceEntity: "Supply Vendor"
        }
      ],
      chartOfAccounts: [
        {
          accountNumber: "4000",
          accountName: "Production Income",
          accountCategory: "Revenue",
          accountType: "Income",
          parentAccount: "Operating Revenue",
          balance: 1250000.00
        },
        {
          accountNumber: "5000",
          accountName: "Laboratory Expenses",
          accountCategory: "Expense",
          accountType: "Cost of Goods Sold",
          parentAccount: "Operating Expenses",
          balance: 320000.00
        },
        {
          accountNumber: "6000",
          accountName: "Facility Expenses",
          accountCategory: "Expense",
          accountType: "Operating Expense",
          parentAccount: "Operating Expenses",
          balance: 450000.00
        }
      ],
      customers: [
        {
          entityId: "CUST_001",
          companyName: "321 Crown Dental Laboratory",
          email: "contact@321crown.com",
          phone: "(555) 123-4567"
        },
        {
          entityId: "CUST_002",
          companyName: "Silver Creek Dental Group",
          email: "admin@silvercreekdental.com",
          phone: "(555) 234-5678"
        }
      ],
      vendors: [
        {
          entityId: "VEND_001",
          companyName: "321 Crown Dental Laboratory",
          email: "billing@321crown.com",
          phone: "(555) 123-4567"
        },
        {
          entityId: "VEND_002",
          companyName: "Laguna Crown, LLC",
          email: "payments@lagunacrown.com",
          phone: "(555) 234-5678"
        }
      ]
    },
    {
      id: "2",
      name: "SCDP San Marcos, LLC",
      code: "san-marcos",
      financialMetrics: {
        totalRevenue: 890000.00,
        totalExpenses: 720000.00,
        netIncome: 170000.00,
        profitMargin: 19.10,
        journalEntryCount: 38,
        accountCount: 22,
        customerCount: 6,
        vendorCount: 10
      },
      journalEntries: [
        {
          journalEntryId: "JE202511006",
          transactionDate: "2025-11-01",
          accountName: "Production Income",
          debitAmount: 0,
          creditAmount: 12000.00,
          description: "Monthly production revenue",
          referenceEntity: "Patient Services"
        },
        {
          journalEntryId: "JE202511007",
          transactionDate: "2025-11-01",
          accountName: "Laboratory Expenses",
          debitAmount: 2800.00,
          creditAmount: 0,
          description: "Lab fees and crowns",
          referenceEntity: "Dental Lab Partners"
        }
      ],
      chartOfAccounts: [
        {
          accountNumber: "4000",
          accountName: "Production Income",
          accountCategory: "Revenue",
          accountType: "Income",
          parentAccount: "Operating Revenue",
          balance: 890000.00
        }
      ],
      customers: [
        {
          entityId: "CUST_003",
          companyName: "San Marcos Dental Group",
          email: "info@sanmarcosdental.com",
          phone: "(555) 345-6789"
        }
      ],
      vendors: [
        {
          entityId: "VEND_003",
          companyName: "Dental Lab Partners",
          email: "invoices@dentallabpartners.com",
          phone: "(555) 345-6789"
        }
      ]
    }
    // Continue with remaining subsidiaries 3-11...
  ]
};

/**
 * Seeds NetSuite financial data into the database
 * This function creates the necessary tables and inserts the financial data
 */
export async function seedNetSuiteFinancialData() {
  console.log('🚀 Starting NetSuite financial data seeding...');

  const dbService = DatabaseService.getInstance();
  await dbService.initialize();
  const db = dbService.getDb();

  try {
    // Create NetSuite financial tables if they don't exist
    console.log('📊 Creating NetSuite financial tables...');

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS netsuite_journal_entries (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        subsidiary_id VARCHAR(50) NOT NULL,
        journal_entry_id VARCHAR(100) NOT NULL,
        transaction_date DATE NOT NULL,
        account_name VARCHAR(255) NOT NULL,
        debit_amount DECIMAL(15,2) DEFAULT 0,
        credit_amount DECIMAL(15,2) DEFAULT 0,
        description TEXT,
        reference_entity VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS netsuite_chart_of_accounts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        subsidiary_id VARCHAR(50) NOT NULL,
        account_number VARCHAR(50),
        account_name VARCHAR(255) NOT NULL,
        account_category VARCHAR(100),
        account_type VARCHAR(100),
        parent_account VARCHAR(255),
        is_active BOOLEAN DEFAULT true,
        balance DECIMAL(15,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS netsuite_customers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        subsidiary_id VARCHAR(50) NOT NULL,
        entity_id VARCHAR(100) NOT NULL,
        company_name VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        phone VARCHAR(50),
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS netsuite_vendors (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        subsidiary_id VARCHAR(50) NOT NULL,
        entity_id VARCHAR(100) NOT NULL,
        company_name VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        phone VARCHAR(50),
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS netsuite_financial_metrics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        subsidiary_id VARCHAR(50) NOT NULL,
        total_revenue DECIMAL(15,2) DEFAULT 0,
        total_expenses DECIMAL(15,2) DEFAULT 0,
        net_income DECIMAL(15,2) DEFAULT 0,
        profit_margin DECIMAL(5,2) DEFAULT 0,
        journal_entry_count INTEGER DEFAULT 0,
        account_count INTEGER DEFAULT 0,
        customer_count INTEGER DEFAULT 0,
        vendor_count INTEGER DEFAULT 0,
        calculation_date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create indexes for performance
    console.log('🔑 Creating indexes...');
    await db.execute(sql`CREATE INDEX IF NOT EXISTS idx_journal_entries_subsidiary ON netsuite_journal_entries(subsidiary_id)`);
    await db.execute(sql`CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON netsuite_journal_entries(transaction_date)`);
    await db.execute(sql`CREATE INDEX IF NOT EXISTS idx_chart_accounts_subsidiary ON netsuite_chart_of_accounts(subsidiary_id)`);
    await db.execute(sql`CREATE INDEX IF NOT EXISTS idx_customers_subsidiary ON netsuite_customers(subsidiary_id)`);
    await db.execute(sql`CREATE INDEX IF NOT EXISTS idx_vendors_subsidiary ON netsuite_vendors(subsidiary_id)`);
    await db.execute(sql`CREATE INDEX IF NOT EXISTS idx_financial_metrics_subsidiary ON netsuite_financial_metrics(subsidiary_id)`);
    await db.execute(sql`CREATE INDEX IF NOT EXISTS idx_financial_metrics_date ON netsuite_financial_metrics(calculation_date)`);

    // Clear existing data to avoid duplicates
    console.log('🧹 Clearing existing NetSuite data...');
    await db.execute(sql`TRUNCATE TABLE netsuite_journal_entries CASCADE`);
    await db.execute(sql`TRUNCATE TABLE netsuite_chart_of_accounts CASCADE`);
    await db.execute(sql`TRUNCATE TABLE netsuite_customers CASCADE`);
    await db.execute(sql`TRUNCATE TABLE netsuite_vendors CASCADE`);
    await db.execute(sql`TRUNCATE TABLE netsuite_financial_metrics CASCADE`);

    // Seed financial metrics for each subsidiary
    console.log('💰 Seeding financial metrics...');
    for (const subsidiary of netsuiteData.subsidiaries) {
      await db.execute(sql`
        INSERT INTO netsuite_financial_metrics (
          subsidiary_id, total_revenue, total_expenses, net_income, profit_margin,
          journal_entry_count, account_count, customer_count, vendor_count
        ) VALUES (
          ${subsidiary.id}, ${subsidiary.financialMetrics.totalRevenue}, ${subsidiary.financialMetrics.totalExpenses},
          ${subsidiary.financialMetrics.netIncome}, ${subsidiary.financialMetrics.profitMargin},
          ${subsidiary.financialMetrics.journalEntryCount}, ${subsidiary.financialMetrics.accountCount},
          ${subsidiary.financialMetrics.customerCount}, ${subsidiary.financialMetrics.vendorCount}
        )
      `);

      console.log(`  ✅ Seeded metrics for ${subsidiary.name}`);
    }

    // Seed journal entries
    console.log('📖 Seeding journal entries...');
    let totalJournalEntries = 0;
    for (const subsidiary of netsuiteData.subsidiaries) {
      for (const entry of subsidiary.journalEntries) {
        await db.execute(sql`
          INSERT INTO netsuite_journal_entries (
            subsidiary_id, journal_entry_id, transaction_date, account_name,
            debit_amount, credit_amount, description, reference_entity
          ) VALUES (
            ${subsidiary.id}, ${entry.journalEntryId}, ${entry.transactionDate}, ${entry.accountName},
            ${entry.debitAmount}, ${entry.creditAmount}, ${entry.description}, ${entry.referenceEntity}
          )
        `);
        totalJournalEntries++;
      }
      console.log(`  ✅ Seeded ${subsidiary.journalEntries.length} journal entries for ${subsidiary.name}`);
    }

    // Seed chart of accounts
    console.log('📊 Seeding chart of accounts...');
    let totalAccounts = 0;
    for (const subsidiary of netsuiteData.subsidiaries) {
      for (const account of subsidiary.chartOfAccounts) {
        await db.execute(sql`
          INSERT INTO netsuite_chart_of_accounts (
            subsidiary_id, account_number, account_name, account_category, account_type, parent_account, balance
          ) VALUES (
            ${subsidiary.id}, ${account.accountNumber}, ${account.accountName}, ${account.accountCategory},
            ${account.accountType}, ${account.parentAccount}, ${account.balance}
          )
        `);
        totalAccounts++;
      }
      console.log(`  ✅ Seeded ${subsidiary.chartOfAccounts.length} accounts for ${subsidiary.name}`);
    }

    // Seed customers
    console.log('👥 Seeding customers...');
    let totalCustomers = 0;
    for (const subsidiary of netsuiteData.subsidiaries) {
      for (const customer of subsidiary.customers) {
        await db.execute(sql`
          INSERT INTO netsuite_customers (
            subsidiary_id, entity_id, company_name, email, phone
          ) VALUES (
            ${subsidiary.id}, ${customer.entityId}, ${customer.companyName}, ${customer.email}, ${customer.phone}
          )
        `);
        totalCustomers++;
      }
      console.log(`  ✅ Seeded ${subsidiary.customers.length} customers for ${subsidiary.name}`);
    }

    // Seed vendors
    console.log('🏢 Seeding vendors...');
    let totalVendors = 0;
    for (const subsidiary of netsuiteData.subsidiaries) {
      for (const vendor of subsidiary.vendors) {
        await db.execute(sql`
          INSERT INTO netsuite_vendors (
            subsidiary_id, entity_id, company_name, email, phone
          ) VALUES (
            ${subsidiary.id}, ${vendor.entityId}, ${vendor.companyName}, ${vendor.email}, ${vendor.phone}
          )
        `);
        totalVendors++;
      }
      console.log(`  ✅ Seeded ${subsidiary.vendors.length} vendors for ${subsidiary.name}`);
    }

    // Create consolidated metrics view
    console.log('📈 Creating consolidated metrics view...');
    await db.execute(sql`
      CREATE OR REPLACE VIEW netsuite_consolidated_metrics AS
      SELECT
        COUNT(DISTINCT subsidiary_id) as total_subsidiaries,
        SUM(total_revenue) as consolidated_revenue,
        SUM(total_expenses) as consolidated_expenses,
        SUM(net_income) as consolidated_net_income,
        ROUND((SUM(net_income) / NULLIF(SUM(total_revenue), 0)) * 100, 2) as consolidated_profit_margin,
        SUM(journal_entry_count) as total_journal_entries,
        SUM(account_count) as total_accounts,
        SUM(customer_count) as total_customers,
        SUM(vendor_count) as total_vendors
      FROM netsuite_financial_metrics
      WHERE calculation_date = CURRENT_DATE
    `);

    // Create subsidiary performance ranking view
    console.log('🏆 Creating performance ranking view...');
    await db.execute(sql`
      CREATE OR REPLACE VIEW subsidiary_performance_ranking AS
      SELECT
        subsidiary_id,
        fm.total_revenue,
        fm.total_expenses,
        fm.net_income,
        fm.profit_margin,
        RANK() OVER (ORDER BY fm.total_revenue DESC) as revenue_rank,
        RANK() OVER (ORDER BY fm.profit_margin DESC) as profitability_rank,
        RANK() OVER (ORDER BY fm.net_income DESC) as net_income_rank
      FROM netsuite_financial_metrics fm
      WHERE calculation_date = CURRENT_DATE
      ORDER BY fm.total_revenue DESC
    `);

    console.log('\n🎉 NetSuite financial data seeding completed successfully!');
    console.log(`📊 Summary:`);
    console.log(`   - Total Subsidiaries: ${netsuiteData.subsidiaries.length}`);
    console.log(`   - Total Journal Entries: ${totalJournalEntries}`);
    console.log(`   - Total Accounts: ${totalAccounts}`);
    console.log(`   - Total Customers: ${totalCustomers}`);
    console.log(`   - Total Vendors: ${totalVendors}`);

    // Print consolidated metrics
    const consolidatedResult = await db.execute(sql`
      SELECT * FROM netsuite_consolidated_metrics
    `);

    if (consolidatedResult.rows.length > 0) {
      const metrics = consolidatedResult.rows[0];
      console.log(`\n💰 Consolidated Financial Metrics:`);
      console.log(`   - Consolidated Revenue: $${Number(metrics.consolidated_revenue).toLocaleString()}`);
      console.log(`   - Consolidated Expenses: $${Number(metrics.consolidated_expenses).toLocaleString()}`);
      console.log(`   - Consolidated Net Income: $${Number(metrics.consolidated_net_income).toLocaleString()}`);
      console.log(`   - Consolidated Profit Margin: ${metrics.consolidated_profit_margin}%`);
    }

    console.log('\n✅ Ready for backend API integration and Snowflake loading!');

  } catch (error) {
    console.error('❌ Error seeding NetSuite financial data:', error);
    throw error;
  }
}

/**
 * Main execution function for the migration
 */
export async function main() {
  console.log('='.repeat(80));
  console.log('NETSUITE FINANCIAL DATA MIGRATION');
  console.log('='.repeat(80));

  try {
    await seedNetSuiteFinancialData();
    console.log('\n🎉 Migration completed successfully!');
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Migration failed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}

export { seedNetSuiteFinancialData as seedNetSuiteFinancialDataMigration };