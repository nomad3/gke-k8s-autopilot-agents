import bcrypt from 'bcryptjs';
import 'dotenv/config';
import { eq } from 'drizzle-orm';
import { DatabaseService } from '../services/database';
import {
  integrations,
  locations,
  practices,
  userPractices,
  users,
  type Integration,
  type Location,
  type NewIntegration,
  type NewLocation,
  type NewPractice,
  type NewUser,
  type NewUserPractice,
  type Practice,
  type User,
  type UserRole
} from './schema';

const defaultOperatingHours: Record<string, [string, string]> = {
  mon: ['08:00', '17:00'],
  tue: ['08:00', '17:00'],
  wed: ['08:00', '17:00'],
  thu: ['08:00', '17:00'],
  fri: ['08:00', '15:00'],
};

async function main() {
  console.log('🌱 Starting database seeding (production mode - real data only)...');

  const dbService = DatabaseService.getInstance();
  await dbService.initialize();
  const db = dbService.getDb();

  const saltRounds = parseInt(process.env.BCRYPT_ROUNDS || '12', 10);

  // ========================================================================
  // 1) PRACTICES - Silver Creek Dental Partners (SCDP) portfolio
  // ========================================================================
  // Real NetSuite Subsidiaries (from TransactionDetail CSV files):
  // See docs/DEMO_DATA_INTEGRITY_REPORT.md for complete mapping
  //
  // "Silver Creek" is the PARENT COMPANY that owns all SCDP subsidiaries
  // This is a single-tenant setup where all practices roll up to silvercreek tenant
  console.log('Creating practices...');
  const practiceSeed: NewPractice[] = [
    {
      name: 'Silver Creek Dental Partners',
      description: 'Silver Creek Dental Partners - Parent Company',
      address: { street: '4520 Executive Dr', city: 'San Diego', state: 'CA', zipCode: '92121', country: 'USA' },
      phone: '858-555-0100',
      email: 'info@silvercreekdental.com',
      website: 'https://silvercreekdental.com',
      tenantId: 'silvercreek', // All subsidiaries use silvercreek tenant
      netsuiteParentId: 'silver_creek_dental_partners',
      isActive: true,
    },
  ];

  let insertedPractices: Practice[] = (await db
    .insert(practices)
    .values(practiceSeed)
    .onConflictDoNothing()
    .returning()) as Practice[];

  if (!insertedPractices.length) {
    console.log('Practices already exist, loading...');
    insertedPractices = (await db.select().from(practices)) as Practice[];
  }
  console.log(`✅ Created ${insertedPractices.length} practices`);

  const practiceByName = new Map<string, Practice>(
    insertedPractices.map((practice: Practice) => [practice.name, practice])
  );

  // ========================================================================
  // 2) LOCATIONS - Real NetSuite subsidiaries from CSV files
  // ========================================================================
  console.log('Creating locations...');

  // Real NetSuite subsidiaries extracted from TransactionDetail CSV files
  // These are the ONLY valid subsidiary names - see docs/DEMO_DATA_INTEGRITY_REPORT.md
  const realNetSuiteSubsidiaries: Array<{ name: string; subsidiaryName: string; csvFiles: string }> = [
    { name: 'San Marcos', subsidiaryName: 'SCDP San Marcos, LLC', csvFiles: '72, 88' },
    { name: 'San Marcos II', subsidiaryName: 'SCDP San Marcos II, LLC', csvFiles: '819' },
    { name: 'Del Sur Ranch', subsidiaryName: 'SCDP Del Sur Ranch, LLC', csvFiles: '165' },
    { name: 'Torrey Pines', subsidiaryName: 'SCDP Torrey Pines, LLC', csvFiles: '263, 658' },
    { name: 'Torrey Highlands', subsidiaryName: 'SCDP Torrey Highlands, LLC', csvFiles: '40' },
    { name: 'Eastlake', subsidiaryName: 'SCDP Eastlake, LLC', csvFiles: '83, 381' },
    { name: 'UTC', subsidiaryName: 'SCDP UTC, LLC', csvFiles: '951' },
    { name: 'Coronado', subsidiaryName: 'SCDP Coronado, LLC', csvFiles: '199' },
    { name: 'Vista', subsidiaryName: 'SCDP Vista, LLC', csvFiles: '868' },
    { name: 'Laguna Hills', subsidiaryName: 'SCDP Laguna Hills, LLC', csvFiles: '232' },
    { name: 'Laguna Hills II', subsidiaryName: 'SCDP Laguna Hills II, LLC', csvFiles: '355' },
    { name: 'Carlsbad', subsidiaryName: 'SCDP Carlsbad, LLC', csvFiles: '942' },
    { name: 'Otay Lakes', subsidiaryName: 'SCDP Otay Lakes, LLC', csvFiles: '599' },
    { name: 'Kearny Mesa', subsidiaryName: 'SCDP Kearny Mesa, LLC', csvFiles: '407' },
    { name: 'Temecula', subsidiaryName: 'SCDP Temecula, LLC', csvFiles: '248' },
    { name: 'Temecula II', subsidiaryName: 'SCDP Temecula II, LLC', csvFiles: '557' },
    { name: 'Theodosis Dental', subsidiaryName: 'Steve P. Theodosis Dental Corporation, PC', csvFiles: '218' },
  ];

  const locationSeed: NewLocation[] = [];
  const parentPractice = insertedPractices[0]; // Silver Creek Dental Partners

  for (const sub of realNetSuiteSubsidiaries) {
    const hours = Object.fromEntries(
      Object.entries(defaultOperatingHours).map(([day, hours]) => [day, [...hours] as [string, string]])
    );

    locationSeed.push({
      practiceId: parentPractice.id,
      name: sub.name,
      address: parentPractice.address,
      phone: parentPractice.phone,
      email: parentPractice.email,
      operatingHours: hours,
      externalSystemId: sub.subsidiaryName.toLowerCase().replace(/[^a-z0-9]/g, '_'),
      externalSystemType: 'netsuite',
      subsidiaryName: sub.subsidiaryName,
      isActive: true,
    });
  }

  let insertedLocations: Location[] = [];
  if (locationSeed.length) {
    insertedLocations = (await db
      .insert(locations)
      .values(locationSeed)
      .onConflictDoNothing()
      .returning()) as Location[];
  }

  if (!insertedLocations.length) {
    console.log('Locations already exist, loading...');
    insertedLocations = (await db.select().from(locations)) as Location[];
  }
  console.log(`✅ Created ${insertedLocations.length} locations`);

  // ========================================================================
  // 3) USERS - Only essential admin and executive users
  // ========================================================================
  console.log('Creating users...');
  const usersSeed: Array<NewUser & { plainPassword: string; practiceNames: string[] }> = [
    {
      email: 'admin@practice.com',
      passwordHash: bcrypt.hashSync('Admin123!', saltRounds),
      role: 'admin' as UserRole,
      firstName: 'System',
      lastName: 'Admin',
      active: true,
      plainPassword: 'Admin123!',
      practiceNames: Array.from(practiceByName.keys()),
    },
    {
      email: 'executive@practice.com',
      passwordHash: bcrypt.hashSync('Demo123!', saltRounds),
      role: 'executive' as UserRole,
      firstName: 'Executive',
      lastName: 'User',
      active: true,
      plainPassword: 'Demo123!',
      practiceNames: Array.from(practiceByName.keys()),
    },
  ];

  let insertedUsers: User[] = (await db
    .insert(users)
    .values(usersSeed.map(({ plainPassword, practiceNames, ...u }) => u))
    .onConflictDoNothing({ target: [users.email] })
    .returning()) as User[];

  if (!insertedUsers.length) {
    console.log('Users already exist, loading...');
    insertedUsers = (await db.select().from(users)) as User[];
  }
  console.log(`✅ Created ${insertedUsers.length} users`);

  const userByEmail = new Map<string, User>(insertedUsers.map((u) => [u.email, u]));

  // ========================================================================
  // 4) USER-PRACTICE RELATIONSHIPS
  // ========================================================================
  console.log('Creating user-practice relationships...');
  const userPracticeSeed: NewUserPractice[] = [];
  for (const u of usersSeed) {
    const insertedUser = userByEmail.get(u.email);
    if (!insertedUser) continue;
    if (!u.role) continue;

    for (const name of u.practiceNames) {
      const p = practiceByName.get(name);
      if (!p) continue;
      userPracticeSeed.push({
        userId: insertedUser.id,
        practiceId: p.id,
        role: u.role,
        isActive: true,
      });
    }
  }

  if (userPracticeSeed.length) {
    await db.insert(userPractices).values(userPracticeSeed).onConflictDoNothing();
  }
  console.log(`✅ Created ${userPracticeSeed.length} user-practice relationships`);

  // ========================================================================
  // 5) NETSUITE INTEGRATIONS - Configure NetSuite integration
  // ========================================================================
  // NetSuite integration for Silver Creek Dental Partners
  // All 17 real subsidiaries are under this parent company
  console.log('Creating NetSuite integrations...');

  // Real NetSuite subsidiary names from CSV files
  const realSubsidiaryNames = [
    'SCDP San Marcos, LLC',
    'SCDP San Marcos II, LLC',
    'SCDP Del Sur Ranch, LLC',
    'SCDP Torrey Pines, LLC',
    'SCDP Torrey Highlands, LLC',
    'SCDP Eastlake, LLC',
    'SCDP UTC, LLC',
    'SCDP Coronado, LLC',
    'SCDP Vista, LLC',
    'SCDP Laguna Hills, LLC',
    'SCDP Laguna Hills II, LLC',
    'SCDP Carlsbad, LLC',
    'SCDP Otay Lakes, LLC',
    'SCDP Kearny Mesa, LLC',
    'SCDP Temecula, LLC',
    'SCDP Temecula II, LLC',
    'Steve P. Theodosis Dental Corporation, PC',
  ];

  const netsuiteIntegrations: NewIntegration[] = [];
  for (const p of insertedPractices) {
    netsuiteIntegrations.push({
      practiceId: p.id,
      type: 'netsuite',
      name: `NetSuite ERP - ${p.name}`,
      status: 'pending',
      config: {
        account_id: process.env.NETSUITE_ACCOUNT_ID || 'placeholder',
        realm: process.env.NETSUITE_REALM || 'placeholder',
        sync_enabled: true,
        sync_frequency: '15m',
        full_sync_schedule: '0 2 * * *',
        sync_datasets: [
          'journal_entries',
          'vendors',
          'customers',
          'employees',
          'accounts',
        ],
        // All 17 real subsidiaries
        subsidiaries: realSubsidiaryNames,
      },
      isActive: true,
    });
  }

  let insertedIntegrations: Integration[] = [];
  if (netsuiteIntegrations.length) {
    insertedIntegrations = (await db
      .insert(integrations)
      .values(netsuiteIntegrations)
      .onConflictDoNothing()
      .returning()) as Integration[];
  }

  if (!insertedIntegrations.length) {
    console.log('NetSuite integrations already exist, loading...');
    insertedIntegrations = (await db
      .select()
      .from(integrations)
      .where(eq(integrations.type, 'netsuite'))) as Integration[];
  }
  console.log(`✅ Created ${insertedIntegrations.length} NetSuite integrations`);

  // ========================================================================
  // SUMMARY
  // ========================================================================
  console.log('\n🎉 Database seeding completed successfully!');
  console.log('\n📊 Summary:');
  console.log(`   • Practices: ${insertedPractices.length} (Silver Creek Dental Partners)`);
  console.log(`   • Locations: ${insertedLocations.length} (17 real NetSuite subsidiaries)`);
  console.log(`   • Users: ${insertedUsers.length}`);
  console.log(`   • User-Practice Links: ${userPracticeSeed.length}`);
  console.log(`   • NetSuite Integrations: ${insertedIntegrations.length}`);
  console.log('\n🔐 Login Credentials:');
  console.log('   Admin:     admin@practice.com / Admin123!');
  console.log('   Executive: executive@practice.com / Demo123!');
  console.log('\n🏢 Real NetSuite Subsidiaries (17 total):');
  console.log('   • SCDP San Marcos, LLC');
  console.log('   • SCDP Del Sur Ranch, LLC');
  console.log('   • SCDP Torrey Pines, LLC');
  console.log('   • SCDP Eastlake, LLC');
  console.log('   • SCDP UTC, LLC');
  console.log('   • ... and 12 more (see docs/DEMO_DATA_INTEGRITY_REPORT.md)');
  console.log('\n✨ Real data comes from:');
  console.log('   • NetSuite CSV files (TransactionDetail-*.csv)');
  console.log('   • Operations Reports (Excel uploads)');
  console.log('   • Snowflake data warehouse (Bronze → Silver → Gold)');
  console.log('\n💡 See docs/DEMO_DATA_INTEGRITY_REPORT.md for mapping details.\n');

  await dbService.close();
  process.exit(0);
}

main().catch((err) => {
  console.error('❌ Seeding failed:', err);
  process.exit(1);
});
