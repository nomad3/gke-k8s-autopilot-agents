/**
 * Backend NetSuite Data Seeding Script - Aligned with MCP Approach
 * Seeds PostgreSQL database with extracted NetSuite data
 * This version aligns with the MCP server seeding approach
 */

import { db } from '../src/database';
import {
  practices,
  locations,
  users,
  userPractices,
  integrations,
  integrationCredentials
} from '../src/database/schema';
import bcrypt from 'bcrypt';
import { eq } from 'drizzle-orm';
import { readFileSync } from 'fs';
import { join } from 'path';

const TENANT_CODE = 'silvercreek';
const PRACTICE_NAME = 'Silver Creek Dental Partners, LLC';

// Silver Creek subsidiaries mapping (aligned with MCP)
const SUBSIDIARY_MAPPING = {
  "1": { name: "Silver Creek Dental Partners, LLC", code: "parent" },
  "2": { name: "SCDP San Marcos, LLC", code: "san-marcos" },
  "3": { name: "SCDP San Marcos II, LLC", code: "san-marcos-2" },
  "4": { name: "SCDP Holdings, LLC", code: "holdings" },
  "5": { name: "SCDP Laguna Hills, LLC", code: "laguna-hills" },
  "6": { name: "SCDP Eastlake, LLC", code: "eastlake" },
  "7": { name: "SCDP Torrey Highlands, LLC", code: "torrey-highlands" },
  "8": { name: "SCDP Vista, LLC", code: "vista" },
  "9": { name: "SCDP Del Sur Ranch, LLC", code: "del-sur-ranch" },
  "10": { name: "SCDP Torrey Pines, LLC", code: "torrey-pines" },
  "11": { name: "SCDP Otay Lakes, LLC", code: "otay-lakes" }
};

interface ExtractedFinancialData {
  subsidiary_id: string;
  subsidiary_name: string;
  journal_entries: Array<{
    id: string;
    journal_entry_id: string;
    transaction_date: string;
    account_name: string;
    debit_amount: number;
    credit_amount: number;
    description: string;
    reference_entity: string;
  }>;
  financial_metrics: {
    total_revenue: number;
    total_expenses: number;
    net_income: number;
    profit_margin: number;
  };
  chart_of_accounts: Array<{
    id: string;
    account_name: string;
    account_category: string;
    account_type: string;
  }>;
}

async function loadExtractedFinancialData(): Promise<ExtractedFinancialData[]> {
  console.log('🔄 Loading extracted NetSuite financial data...');

  try {
    // Try to load from API extraction first, fallback to CSV extraction
    const apiDataPath = '/tmp/netsuite-api-extracted/subsidiary_data.json';
    const csvDataPath = '/tmp/netsuite-extracted/extraction_summary.json';

    let dataSource;
    try {
      // Try API data first
      const apiData = JSON.parse(readFileSync(apiDataPath, 'utf8'));
      dataSource = apiData;
      console.log('✅ Using API-extracted data');
    } catch {
      // Fallback to CSV data
      const csvData = JSON.parse(readFileSync(csvDataPath, 'utf8'));
      dataSource = csvData;
      console.log('✅ Using CSV-extracted data');
    }

    // Transform data to our format
    const financialData: ExtractedFinancialData[] = [];

    for (const [subsidiaryId, subsidiaryData] of Object.entries(dataSource)) {
      if (subsidiaryData.error || !subsidiaryData.journal_entries) {
        console.log(`⚠️  Skipping subsidiary ${subsidiaryId} due to extraction error`);
        continue;
      }

      const journalEntries = subsidiaryData.journal_entries || [];
      const financialMetrics = subsidiaryData.financial_metrics || {};
      const chartOfAccounts = subsidiaryData.chart_of_accounts || [];

      financialData.push({
        subsidiary_id: subsidiaryId,
        subsidiary_name: SUBSIDIARY_MAPPING[subsidiaryId]?.name || `Subsidiary ${subsidiaryId}`,
        journal_entries: journalEntries.map(entry => ({
          id: entry.id || `JE_${subsidiaryId}_${Date.now()}`,
          journal_entry_id: entry.journal_entry_id || entry.id,
          transaction_date: entry.transaction_date || new Date().toISOString(),
          account_name: entry.account_name || 'Unknown',
          debit_amount: entry.debit_amount || 0,
          credit_amount: entry.credit_amount || 0,
          description: entry.description || '',
          reference_entity: entry.reference_entity || ''
        })),
        financial_metrics: {
          total_revenue: financialMetrics.total_revenue || 0,
          total_expenses: financialMetrics.total_expenses || 0,
          net_income: financialMetrics.net_income || 0,
          profit_margin: financialMetrics.profit_margin || 0
        },
        chart_of_accounts: chartOfAccounts.map(account => ({
          id: account.id || `ACCT_${subsidiaryId}_${Date.now()}`,
          account_name: account.account_name || 'Unknown',
          account_category: account.account_category || 'Other',
          account_type: account.account_type || 'Other'
        }))
      });
    }

    console.log(`✅ Loaded financial data for ${financialData.length} subsidiaries`);

    // Print summary
    financialData.forEach(data => {
      console.log(`\n🏢 ${data.subsidiary_name}:`);
      console.log(`   Journal Entries: ${data.journal_entries.length}`);
      console.log(`   Revenue: $${data.financial_metrics.total_revenue.toLocaleString()}`);
      console.log(`   Expenses: $${data.financial_metrics.total_expenses.toLocaleString()}`);
      console.log(`   Net Income: $${data.financial_metrics.net_income.toLocaleString()}`);
      console.log(`   Profit Margin: ${data.financial_metrics.profit_margin.toFixed(2)}%`);
      console.log(`   Chart of Accounts: ${data.chart_of_accounts.length} accounts`);
    });

    return financialData;

  } catch (error) {
    console.error('❌ Error loading extracted financial data:', error);
    // Return empty array if no data found
    return [];
  }
}

async function seedPracticeWithFinancialData(financialData: ExtractedFinancialData[]) {
  console.log('🌱 Seeding practice with financial data...');

  try {
    // Calculate consolidated metrics
    const consolidatedMetrics = calculateConsolidatedMetrics(financialData);

    // Create parent practice
    const [practice] = await db.insert(practices).values({
      name: PRACTICE_NAME,
      description: `Multi-location dental practice group with ${financialData.length} active locations in California`,
      address: {
        street: '1234 Healthcare Blvd',
        city: 'San Diego',
        state: 'CA',
        zipCode: '92101',
        country: 'USA'
      },
      phone: '(858) 555-0100',
      email: 'info@silvercreekdp.com',
      website: 'https://silvercreekdp.com',
      tenantId: TENANT_CODE,
      netsuiteParentId: '1',
      settings: {
        financialMetrics: {
          totalRevenue: consolidatedMetrics.totalRevenue,
          totalExpenses: consolidatedMetrics.totalExpenses,
          netIncome: consolidatedMetrics.netIncome,
          averageProfitMargin: consolidatedMetrics.averageProfitMargin,
          activeLocations: financialData.length
        },
        subsidiaries: Object.values(SUBSIDIARY_MAPPING),
        multiLocation: true,
        primaryCurrency: 'USD',
        timezone: 'America/Los_Angeles'
      },
      isActive: true
    }).returning();

    console.log(`✅ Created practice: ${practice.name}`);
    console.log(`   Consolidated Revenue: $${consolidatedMetrics.totalRevenue.toLocaleString()}`);
    console.log(`   Consolidated Net Income: $${consolidatedMetrics.netIncome.toLocaleString()}`);
    console.log(`   Active Locations: ${financialData.length}`);

    return practice;

  } catch (error) {
    console.error('❌ Error seeding practice with financial data:', error);
    throw error;
  }
}

function calculateConsolidatedMetrics(financialData: ExtractedFinancialData[]) {
  const totalRevenue = financialData.reduce((sum, data) => sum + data.financial_metrics.total_revenue, 0);
  const totalExpenses = financialData.reduce((sum, data) => sum + data.financial_metrics.total_expenses, 0);
  const netIncome = financialData.reduce((sum, data) => sum + data.financial_metrics.net_income, 0);
  const averageProfitMargin = financialData.length > 0
    ? financialData.reduce((sum, data) => sum + data.financial_metrics.profit_margin, 0) / financialData.length
    : 0;

  return {
    totalRevenue,
    totalExpenses,
    netIncome,
    averageProfitMargin
  };
}

async function seedLocationsWithFinancialData(financialData: ExtractedFinancialData[], practice: any) {
  console.log('🏢 Seeding locations with financial data...');

  try {
    const seededLocations = [];

    for (const data of financialData) {
      const subsidiaryInfo = SUBSIDIARY_MAPPING[data.subsidiary_id];

      // Create location with financial data
      const [location] = await db.insert(locations).values({
        practiceId: practice.id,
        name: data.subsidiary_name,
        subsidiaryName: data.subsidiary_name,
        externalSystemId: data.subsidiary_id,
        externalSystemType: 'netsuite',
        address: {
          street: `${subsidiaryInfo.code.replace('-', ' ').title()} Plaza`,
          city: 'San Diego',
          state: 'CA',
          zipCode: '92101',
          country: 'USA'
        },
        phone: `(858) 555-${data.subsidiary_id.padStart(4, '0')}`,
        email: `${subsidiaryInfo.code}@silvercreekdp.com`,
        operatingHours: {
          monday: { open: '08:00', close: '17:00' },
          tuesday: { open: '08:00', close: '17:00' },
          wednesday: { open: '08:00', close: '17:00' },
          thursday: { open: '08:00', close: '17:00' },
          friday: { open: '08:00', close: '17:00' },
          saturday: { open: '09:00', close: '13:00' },
          sunday: { open: null, close: null }
        },
        settings: {
          financialMetrics: data.financial_metrics,
          journalEntryCount: data.journal_entries.length,
          chartOfAccountsCount: data.chart_of_accounts.length
        },
        isActive: true
      }).returning();

      seededLocations.push(location);
      console.log(`  ✅ Created location: ${location.name}`);
      console.log(`     Revenue: $${data.financial_metrics.total_revenue.toLocaleString()}`);
      console.log(`     Net Income: $${data.financial_metrics.net_income.toLocaleString()}`);
      console.log(`     Journal Entries: ${data.journal_entries.length}`);
    }

    console.log(`✅ Seeded ${seededLocations.length} locations`);
    return seededLocations;

  } catch (error) {
    console.error('❌ Error seeding locations with financial data:', error);
    throw error;
  }
}

async function createFinancialIntegration(practice: any) {
  console.log('💰 Creating financial data integration...');

  try {
    // Create NetSuite financial integration
    const [integration] = await db.insert(integrations).values({
      practiceId: practice.id,
      type: 'netsuite',
      name: 'NetSuite Financial Data',
      status: 'connected',
      config: {
        account: process.env.NETSUITE_ACCOUNT_ID || '7048582',
        apiUrl: 'https://7048582.suitetalk.api.netsuite.com/services/rest/record/v1',
        recordTypes: [
          'journalEntry',
          'account',
          'invoice',
          'customerPayment',
          'vendorBill',
          'customer',
          'vendor'
        ],
        syncConfig: {
          frequency: '15m',
          fullSync: '0 2 * * *', // Daily at 2 AM
          incremental: true
        }
      },
      lastSync: new Date(),
      isActive: true
    }).returning();

    console.log(`✅ Created financial integration for ${practice.name}`);
    return integration;

  } catch (error) {
    console.error('❌ Error creating financial integration:', error);
    throw error;
  }
}

async function generateFinancialComparisonReport(financialData: ExtractedFinancialData[]) {
  console.log('\n📊 Generating Financial Comparison Report...');
  console.log('='.repeat(60));

  // Sort by revenue
  const byRevenue = [...financialData].sort((a, b) => b.financial_metrics.total_revenue - a.financial_metrics.total_revenue);
  const byProfitMargin = [...financialData].sort((a, b) => b.financial_metrics.profit_margin - a.financial_metrics.profit_margin);
  const byNetIncome = [...financialData].sort((a, b) => b.financial_metrics.net_income - a.financial_metrics.net_income);

  console.log('\n🏆 Top Performers by Revenue:');
  byRevenue.slice(0, 5).forEach((data, index) => {
    console.log(`   ${index + 1}. ${data.subsidiary_name}: $${data.financial_metrics.total_revenue.toLocaleString()}`);
  });

  console.log('\n🏆 Top Performers by Profit Margin:');
  byProfitMargin.slice(0, 5).forEach((data, index) => {
    console.log(`   ${index + 1}. ${data.subsidiary_name}: ${data.financial_metrics.profit_margin.toFixed(2)}%`);
  });

  console.log('\n🏆 Top Performers by Net Income:');
  byNetIncome.slice(0, 5).forEach((data, index) => {
    console.log(`   ${index + 1}. ${data.subsidiary_name}: $${data.financial_metrics.net_income.toLocaleString()}`);
  });

  // Calculate averages
  const avgRevenue = financialData.reduce((sum, data) => sum + data.financial_metrics.total_revenue, 0) / financialData.length;
  const avgExpenses = financialData.reduce((sum, data) => sum + data.financial_metrics.total_expenses, 0) / financialData.length;
  const avgNetIncome = financialData.reduce((sum, data) => sum + data.financial_metrics.net_income, 0) / financialData.length;
  const avgProfitMargin = financialData.reduce((sum, data) => sum + data.financial_metrics.profit_margin, 0) / financialData.length;

  console.log('\n📈 Performance Averages:');
  console.log(`   Average Revenue: $${avgRevenue.toLocaleString()}`);
  console.log(`   Average Expenses: $${avgExpenses.toLocaleString()}`);
  console.log(`   Average Net Income: $${avgNetIncome.toLocaleString()}`);
  console.log(`   Average Profit Margin: ${avgProfitMargin.toFixed(2)}%`);

  console.log('\n' + '='.repeat(60));

  return {
    rankings: {
      byRevenue: byRevenue.map(d => ({ name: d.subsidiary_name, value: d.financial_metrics.total_revenue })),
      byProfitMargin: byProfitMargin.map(d => ({ name: d.subsidiary_name, value: d.financial_metrics.profit_margin })),
      byNetIncome: byNetIncome.map(d => ({ name: d.subsidiary_name, value: d.financial_metrics.net_income }))
    },
    averages: {
      revenue: avgRevenue,
      expenses: avgExpenses,
      netIncome: avgNetIncome,
      profitMargin: avgProfitMargin
    }
  };
}

async function verifyBackendSeeding(financialData: ExtractedFinancialData[], practice: any, locations: any[]) {
  console.log('🔍 Verifying backend seeding...');

  try {
    // Verify practice
    const [verifiedPractice] = await db.select()
      .from(practices)
      .where(eq(practices.id, practice.id));

    if (!verifiedPractice) {
      throw new Error('Practice not found after seeding');
    }

    console.log(`✅ Practice verified: ${verifiedPractice.name}`);

    // Verify locations
    const verifiedLocations = await db.select()
      .from(locations)
      .where(eq(locations.practiceId, practice.id));

    if (verifiedLocations.length !== locations.length) {
      throw new Error(`Location count mismatch: expected ${locations.length}, got ${verifiedLocations.length}`);
    }

    console.log(`✅ Locations verified: ${verifiedLocations.length} locations`);

    // Verify financial data integration
    const verifiedIntegration = await db.select()
      .from(integrations)
      .where(eq(integrations.practiceId, practice.id))
      .where(eq(integrations.type, 'netsuite'));

    if (verifiedIntegration.length === 0) {
      throw new Error('NetSuite integration not found after seeding');
    }

    console.log(`✅ NetSuite integration verified`);

    // Verify financial data availability
    const totalJournalEntries = financialData.reduce((sum, data) => sum + data.journal_entries.length, 0);
    const totalChartOfAccounts = financialData.reduce((sum, data) => sum + data.chart_of_accounts.length, 0);

    console.log(`✅ Financial data ready:`);
    console.log(`   - ${totalJournalEntries} journal entries across all subsidiaries`);
    console.log(`   - ${totalChartOfAccounts} chart of accounts entries`);
    console.log(`   - ${financialData.length} active subsidiaries`);

    return {
      practice: verifiedPractice,
      locations: verifiedLocations,
      integration: verifiedIntegration[0],
      financialData: {
        journalEntries: totalJournalEntries,
        chartOfAccounts: totalChartOfAccounts,
        subsidiaries: financialData.length
      }
    };

  } catch (error) {
    console.error('❌ Error verifying backend seeding:', error);
    throw error;
  }
}

async function seedNetSuiteBackendData() {
  console.log('🚀 Starting NetSuite backend data seeding (aligned with MCP)...');
  console.log('='.repeat(60));

  try {
    // 1. Load extracted financial data
    const financialData = await loadExtractedFinancialData();

    if (financialData.length === 0) {
      console.log('⚠️  No financial data found. Please run NetSuite extraction first.');
      return {
        success: false,
        error: 'No financial data available'
      };
    }

    // 2. Seed practice with consolidated financial metrics
    const practice = await seedPracticeWithFinancialData(financialData);

    // 3. Seed locations with individual subsidiary financial data
    const locations = await seedLocationsWithFinancialData(financialData, practice);

    // 4. Create financial integration
    const integration = await createFinancialIntegration(practice);

    // 5. Generate financial comparison report
    const comparisonReport = await generateFinancialComparisonReport(financialData);

    // 6. Verify seeding
    const verification = await verifyBackendSeeding(financialData, practice, locations);

    console.log('\n' + '='.repeat(60));
    console.log('🎉 NETSUITE BACKEND DATA SEEDING COMPLETED SUCCESSFULLY!');
    console.log('='.repeat(60));

    console.log('\n📋 Seeding Summary:');
    console.log(`   Practice: ${practice.name}`);
    console.log(`   Locations: ${locations.length} subsidiaries`);
    console.log(`   NetSuite Integration: ${integration.name}`);
    console.log(`   Financial Records: ${verification.financialData.journalEntries} journal entries`);
    console.log(`   Chart of Accounts: ${verification.financialData.chartOfAccounts} accounts`);

    console.log('\n🎯 Ready for:');
    console.log('   ✓ Snowflake data loading (Bronze → Silver → Gold)');
    console.log('   ✓ Financial analytics and KPI calculation');
    console.log('   ✓ Multi-location dashboard with subsidiary comparison');
    console.log('   ✓ Real-time financial metrics and trends');
    console.log('   ✓ PMS vs NetSuite reconciliation analysis');

    return {
      success: true,
      practice,
      locations,
      integration,
      comparisonReport,
      financialData
    };

  } catch (error) {
    console.error('❌ NetSuite backend data seeding failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Main execution
if (require.main === module) {
  seedNetSuiteBackendData()
    .then((result) => {
      if (result.success) {
        console.log('\n✅ All NetSuite backend data has been successfully seeded!');
        console.log('🔄 Next step: Load data into Snowflake for analytics and dashboard display');
        process.exit(0);
      } else {
        console.error('\n❌ Backend seeding failed:', result.error);
        process.exit(1);
      }
    })
    .catch((error) => {
      console.error('\n❌ Unexpected error:', error);
      process.exit(1);
    });
}

export { seedNetSuiteBackendData, loadExtractedFinancialData };