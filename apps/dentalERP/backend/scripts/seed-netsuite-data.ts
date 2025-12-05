/**
 * Backend NetSuite Data Seeding Script
 * Seeds PostgreSQL database with extracted NetSuite backup data
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

const TENANT_CODE = 'silvercreek';
const PRACTICE_NAME = 'Silver Creek Dental Partners, LLC';

interface ExtractedData {
  locations: any[];
  users: any[];
  chartOfAccounts: any[];
  transactions: {
    journalEntries: any[];
    bills: any[];
    invoices: any[];
    customerPayments: any[];
    vendorBills: any[];
  };
}

async function loadExtractedData(): Promise<ExtractedData> {
  console.log('🔄 Loading extracted NetSuite data...');

  try {
    // Load extracted data from files
    const fs = require('fs');
    const path = require('path');

    const extractedDir = '/tmp/netsuite-extracted';

    const locations = JSON.parse(fs.readFileSync(path.join(extractedDir, 'locations.json'), 'utf8'));
    const users = JSON.parse(fs.readFileSync(path.join(extractedDir, 'users.json'), 'utf8'));
    const chartOfAccounts = JSON.parse(fs.readFileSync(path.join(extractedDir, 'chart_of_accounts.json'), 'utf8'));

    // Load transaction data
    const journalEntries = JSON.parse(fs.readFileSync(path.join(extractedDir, 'journal_entries.json'), 'utf8'));

    console.log(`✅ Loaded data:`);
    console.log(`  - ${locations.length} locations`);
    console.log(`  - ${users.length} users`);
    console.log(`  - ${chartOfAccounts.length} chart of accounts`);
    console.log(`  - ${journalEntries.length} journal entries`);

    return {
      locations,
      users,
      chartOfAccounts,
      transactions: {
        journalEntries,
        bills: [],
        invoices: [],
        customerPayments: [],
        vendorBills: []
      }
    };
  } catch (error) {
    console.error('❌ Error loading extracted data:', error);
    throw error;
  }
}

async function seedPracticeAndLocations(extractedData: ExtractedData) {
  console.log('🌱 Seeding practice and locations...');

  try {
    // 1. Create parent practice
    const [practice] = await db.insert(practices).values({
      name: PRACTICE_NAME,
      description: 'Multi-location dental practice group with 9 locations in California',
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
      netsuiteParentId: '1',  // NetSuite parent company ID
      isActive: true
    }).returning();

    console.log(`✅ Created practice: ${practice.name}`);

    // 2. Create locations for each subsidiary
    const seededLocations = [];

    for (const location of extractedData.locations) {
      const [seededLocation] = await db.insert(locations).values({
        practiceId: practice.id,
        name: location.name,
        subsidiaryName: location.subsidiary_name,
        externalSystemId: location.external_system_id,
        externalSystemType: location.external_system_type,
        address: location.address,
        phone: location.phone,
        email: location.email,
        operatingHours: location.operating_hours,
        isActive: location.is_active
      }).returning();

      seededLocations.push(seededLocation);
      console.log(`  ✅ Created location: ${seededLocation.name}`);
    }

    console.log(`✅ Seeded ${seededLocations.length} locations`);
    return { practice, locations: seededLocations };

  } catch (error) {
    console.error('❌ Error seeding practice and locations:', error);
    throw error;
  }
}

async function seedUsers(extractedData: ExtractedData, practice: any) {
  console.log('👥 Seeding users...');

  try {
    const seededUsers = [];
    const userPracticeLinks = [];

    for (const user of extractedData.users) {
      // Hash password (using default password for seeding)
      const hashedPassword = await bcrypt.hash('dentalerp2025', 10);

      const [seededUser] = await db.insert(users).values({
        email: user.email,
        passwordHash: hashedPassword,
        firstName: user.first_name,
        lastName: user.last_name,
        role: user.role,
        phone: user.phone,
        active: user.active
      }).returning();

      seededUsers.push(seededUser);

      // Link user to practice
      const [userPractice] = await db.insert(userPractices).values({
        userId: seededUser.id,
        practiceId: practice.id,
        role: user.role,
        permissions: user.role === 'executive' ? ['all'] :
                    user.role === 'manager' ? ['finance', 'operations'] :
                    ['read'],
        isActive: user.active
      }).returning();

      userPracticeLinks.push(userPractice);
      console.log(`  ✅ Created user: ${seededUser.firstName} ${seededUser.lastName} (${seededUser.role})`);
    }

    console.log(`✅ Seeded ${seededUsers.length} users`);
    return { users: seededUsers, userPractices: userPracticeLinks };

  } catch (error) {
    console.error('❌ Error seeding users:', error);
    throw error;
  }
}

async function seedNetSuiteIntegration(practice: any) {
  console.log('🔗 Seeding NetSuite integration...');

  try {
    // Create NetSuite integration
    const [integration] = await db.insert(integrations).values({
      practiceId: practice.id,
      type: 'netsuite',
      name: 'NetSuite ERP',
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
          'vendor',
          'inventoryItem',
          'subsidiary'
        ]
      },
      lastSync: new Date(),
      isActive: true
    }).returning();

    console.log(`✅ Created NetSuite integration for ${practice.name}`);
    return integration;

  } catch (error) {
    console.error('❌ Error seeding NetSuite integration:', error);
    throw error;
  }
}

async function verifySeeding(extractedData: ExtractedData, practice: any, locations: any[], users: any[]) {
  console.log('🔍 Verifying seeded data...');

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

    // Verify users
    const verifiedUsers = await db.select()
      .from(users)
      .where(eq(users.active, true));

    if (verifiedUsers.length !== users.length) {
      throw new Error(`User count mismatch: expected ${users.length}, got ${verifiedUsers.length}`);
    }

    console.log(`✅ Users verified: ${verifiedUsers.length} users`);

    // Verify NetSuite integration
    const verifiedIntegration = await db.select()
      .from(integrations)
      .where(eq(integrations.practiceId, practice.id))
      .where(eq(integrations.type, 'netsuite'));

    if (verifiedIntegration.length === 0) {
      throw new Error('NetSuite integration not found after seeding');
    }

    console.log(`✅ NetSuite integration verified`);

    // Verify financial data availability
    const journalEntryCount = extractedData.transactions.journalEntries.length;
    console.log(`✅ Financial data ready: ${journalEntryCount} journal entries`);

    return {
      practice: verifiedPractice,
      locations: verifiedLocations,
      users: verifiedUsers,
      integration: verifiedIntegration[0],
      financialData: {
        journalEntries: journalEntryCount,
        chartOfAccounts: extractedData.chartOfAccounts.length
      }
    };

  } catch (error) {
    console.error('❌ Error verifying seeded data:', error);
    throw error;
  }
}

async function generateFinancialSummary(extractedData: ExtractedData) {
  console.log('📊 Generating financial summary...');

  const journalEntries = extractedData.transactions.journalEntries;

  if (journalEntries.length === 0) {
    console.log('⚠️  No journal entries found for summary');
    return;
  }

  // Group by subsidiary
  const subsidiarySummary = {};

  for (const entry of journalEntries) {
    const subsidiaryId = entry.subsidiary_id || '1';

    if (!subsidiarySummary[subsidiaryId]) {
      subsidiarySummary[subsidiaryId] = {
        subsidiaryId,
        totalDebits: 0,
        totalCredits: 0,
        entryCount: 0,
        netAmount: 0
      };
    }

    subsidiarySummary[subsidiaryId].totalDebits += entry.debit_amount || 0;
    subsidiarySummary[subsidiaryId].totalCredits += entry.credit_amount || 0;
    subsidiarySummary[subsidiaryId].entryCount += 1;
    subsidiarySummary[subsidiaryId].netAmount += (entry.debit_amount || 0) - (entry.credit_amount || 0);
  }

  console.log('\n📈 Financial Summary by Subsidiary:');
  console.log('='.repeat(60));

  for (const [subId, summary] of Object.entries(subsidiarySummary)) {
    const subName = summary.subsidiaryId === '1' ? 'Parent Company' : `SCDP ${summary.subsidiaryId}`;
    console.log(`\n🏢 ${subName}:`);
    console.log(`   Journal Entries: ${summary.entryCount}`);
    console.log(`   Total Debits: $${summary.totalDebits.toLocaleString()}`);
    console.log(`   Total Credits: $${summary.totalCredits.toLocaleString()}`);
    console.log(`   Net Amount: $${summary.netAmount.toLocaleString()}`);
  }

  console.log('\n' + '='.repeat(60));

  // Overall summary
  const totalEntries = journalEntries.length;
  const totalDebits = journalEntries.reduce((sum, entry) => sum + (entry.debit_amount || 0), 0);
  const totalCredits = journalEntries.reduce((sum, entry) => sum + (entry.credit_amount || 0), 0);
  const netAmount = totalDebits - totalCredits;

  console.log(`\n📊 Overall Financial Summary:`);
  console.log(`   Total Journal Entries: ${totalEntries}`);
  console.log(`   Total Debits: $${totalDebits.toLocaleString()}`);
  console.log(`   Total Credits: $${totalCredits.toLocaleString()}`);
  console.log(`   Net Amount: $${netAmount.toLocaleString()}`);

  return {
    subsidiarySummary,
    overallSummary: {
      totalEntries,
      totalDebits,
      totalCredits,
      netAmount
    }
  };
}

async function seedNetSuiteData() {
  console.log('🚀 Starting NetSuite data seeding process...');
  console.log('='.repeat(60));

  try {
    // 1. Load extracted data
    const extractedData = await loadExtractedData();

    // 2. Seed practice and locations
    const { practice, locations } = await seedPracticeAndLocations(extractedData);

    // 3. Seed users
    const { users, userPractices } = await seedUsers(extractedData, practice);

    // 4. Seed NetSuite integration
    const integration = await seedNetSuiteIntegration(practice);

    // 5. Verify seeding
    const verification = await verifySeeding(extractedData, practice, locations, users);

    // 6. Generate financial summary
    const financialSummary = await generateFinancialSummary(extractedData);

    console.log('\n' + '='.repeat(60));
    console.log('🎉 NETSUITE DATA SEEDING COMPLETED SUCCESSFULLY!');
    console.log('='.repeat(60));

    console.log('\n📋 Seeding Summary:');
    console.log(`   Practice: ${practice.name}`);
    console.log(`   Locations: ${locations.length} subsidiaries`);
    console.log(`   Users: ${users.length} users`);
    console.log(`   NetSuite Integration: ${integration.name}`);
    console.log(`   Financial Records: ${verification.financialData.journalEntries} journal entries`);
    console.log(`   Chart of Accounts: ${verification.financialData.chartOfAccounts} accounts`);

    return {
      success: true,
      practice,
      locations,
      users,
      integration,
      financialSummary
    };

  } catch (error) {
    console.error('❌ NetSuite data seeding failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Main execution
if (require.main === module) {
  seedNetSuiteData()
    .then((result) => {
      if (result.success) {
        console.log('\n✅ All NetSuite data has been successfully seeded!');
        console.log('🔄 Next step: Load financial data into Snowflake for analytics');
        process.exit(0);
      } else {
        console.error('\n❌ Seeding failed:', result.error);
        process.exit(1);
      }
    })
    .catch((error) => {
      console.error('\n❌ Unexpected error:', error);
      process.exit(1);
    });
}

export { seedNetSuiteData, loadExtractedData };