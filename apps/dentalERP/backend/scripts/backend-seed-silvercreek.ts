/**
 * Backend Seed Script - Silver Creek Dental Partners
 * Seeds practices and locations based on real NetSuite data
 */

import { db } from '../src/database';
import { practices, locations, users, userPractices } from '../src/database/schema';
import bcrypt from 'bcrypt';

async function seedSilverCreek() {
  console.log('🌱 Seeding Silver Creek Dental Partners...');

  // 1. Create Parent Practice (Silver Creek Dental Partners, LLC)
  const [practice] = await db.insert(practices).values({
    name: 'Silver Creek Dental Partners, LLC',
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
    tenantId: 'silvercreek',  // Links to MCP tenant
    netsuiteParentId: '1',  // Parent Company internal ID in NetSuite
    isActive: true
  }).returning();

  console.log(`✅ Created practice: ${practice.name}`);

  // 2. Create 9 Subsidiary Locations (from custjoblist.csv)
  const subsidiaries = [
    { name: 'SCDP San Marcos, LLC', code: 'san-marcos', subsidiaryId: '2' },
    { name: 'SCDP San Marcos II, LLC', code: 'san-marcos-2', subsidiaryId: '3' },
    { name: 'SCDP Holdings, LLC', code: 'holdings', subsidiaryId: '4' },
    { name: 'SCDP Laguna Hills, LLC', code: 'laguna-hills', subsidiaryId: '5' },
    { name: 'SCDP Eastlake, LLC', code: 'eastlake', subsidiaryId: '6' },
    { name: 'SCDP Torrey Highlands, LLC', code: 'torrey-highlands', subsidiaryId: '7' },
    { name: 'SCDP Vista, LLC', code: 'vista', subsidiaryId: '8' },
    { name: 'SCDP Del Sur Ranch, LLC', code: 'del-sur-ranch', subsidiaryId: '9' },
    { name: 'SCDP Torrey Pines, LLC', code: 'torrey-pines', subsidiaryId: '10' },
    { name: 'SCDP Otay Lakes, LLC', code: 'otay-lakes', subsidiaryId: '11' },
  ];

  for (const sub of subsidiaries) {
    await db.insert(locations).values({
      practiceId: practice.id,
      name: sub.name,
      subsidiaryName: sub.name,
      externalSystemId: sub.subsidiaryId,
      externalSystemType: 'netsuite',
      address: {
        street: `${sub.code} Dental Plaza`,
        city: 'San Diego',
        state: 'CA',
        zipCode: '92101',
        country: 'USA'
      },
      phone: `(858) 555-${sub.subsidiaryId.padStart(4, '0')}`,
      email: `${sub.code}@silvercreekdp.com`,
      operatingHours: {
        monday: { open: '08:00', close: '17:00' },
        tuesday: { open: '08:00', close: '17:00' },
        wednesday: { open: '08:00', close: '17:00' },
        thursday: { open: '08:00', close: '17:00' },
        friday: { open: '08:00', close: '17:00' },
        saturday: { open: '09:00', close: '13:00' },
        sunday: { open: null, close: null }
      },
      isActive: true
    });

    console.log(`  ✅ Created location: ${sub.name}`);
  }

  // 3. Create users (from employeelist.csv)
  const hashedPassword = await bcrypt.hash('dentalerp2025', 10);

  const brad = await db.insert(users).values({
    email: 'bstarkweather@silvercreekhealthcare.com',
    passwordHash: hashedPassword,
    firstName: 'Brad',
    lastName: 'Starkweather',
    role: 'executive',
    phone: '(858) 555-1000',
    active: true
  }).returning();

  const barbara = await db.insert(users).values({
    email: 'bmarra@silvercreekdp.com',
    passwordHash: hashedPassword,
    firstName: 'Barbara',
    lastName: 'Marra',
    role: 'manager',
    phone: '(858) 555-1001',
    active: true
  }).returning();

  const lindsey = await db.insert(users).values({
    email: 'lschmidt@303accounting.com',
    passwordHash: hashedPassword,
    firstName: 'Lindsey',
    lastName: 'Schmidt',
    role: 'manager',
    phone: '(303) 877-7685',
    active: true
  }).returning();

  // 4. Link users to practice
  await db.insert(userPractices).values([
    {
      userId: brad[0].id,
      practiceId: practice.id,
      role: 'executive',
      permissions: ['all'],
      isActive: true
    },
    {
      userId: barbara[0].id,
      practiceId: practice.id,
      role: 'manager',
      permissions: ['finance', 'operations'],
      isActive: true
    },
    {
      userId: lindsey[0].id,
      practiceId: practice.id,
      role: 'manager',
      permissions: ['finance', 'accounting'],
      isActive: true
    }
  ]);

  console.log('✅ Seeded 3 users and linked to practice');
  console.log(`\n✨ Silver Creek setup complete!`);
  console.log(`   Practice: ${practice.name}`);
  console.log(`   Locations: ${subsidiaries.length}`);
  console.log(`   Users: 3 (Brad CFO, Barbara Manager, Lindsey Accountant)`);
  console.log(`\nLogin credentials:`);
  console.log(`   Email: bstarkweather@silvercreekhealthcare.com`);
  console.log(`   Password: dentalerp2025`);
}

seedSilverCreek().catch(console.error).finally(() => process.exit());
