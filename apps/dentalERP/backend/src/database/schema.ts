import { relations } from 'drizzle-orm';
import { boolean, integer, jsonb, pgEnum, pgTable, text, timestamp, uuid, varchar, index, uniqueIndex } from 'drizzle-orm/pg-core';

// Enums
export const userRoleEnum = pgEnum('user_role', ['admin', 'executive', 'manager', 'clinician', 'staff']);
export const integrationStatusEnum = pgEnum('integration_status', ['connected', 'disconnected', 'error', 'pending']);
export const appointmentStatusEnum = pgEnum('appointment_status', ['scheduled', 'confirmed', 'checked_in', 'in_progress', 'completed', 'cancelled', 'no_show']);
export const patientStatusEnum = pgEnum('patient_status', ['active', 'inactive', 'archived']);
export const widgetTypeEnum = pgEnum('widget_type', ['metric', 'chart', 'list', 'action']);

// Users table
export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  passwordHash: varchar('password_hash', { length: 255 }).notNull(),
  firstName: varchar('first_name', { length: 100 }).notNull(),
  lastName: varchar('last_name', { length: 100 }).notNull(),
  role: userRoleEnum('role').notNull().default('staff'),
  avatar: text('avatar'),
  phone: varchar('phone', { length: 20 }),
  active: boolean('active').notNull().default(true),
  lastLogin: timestamp('last_login'),
  preferences: jsonb('preferences').default({}),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Practices table
export const practices = pgTable('practices', {
  id: uuid('id').primaryKey().defaultRandom(),
  name: varchar('name', { length: 255 }).notNull(),
  description: text('description'),
  address: jsonb('address').notNull(), // {street, city, state, zipCode, country}
  phone: varchar('phone', { length: 20 }),
  email: varchar('email', { length: 255 }),
  website: varchar('website', { length: 255 }),
  taxId: varchar('tax_id', { length: 50 }),
  tenantId: varchar('tenant_id', { length: 50 }), // Links to MCP tenant.tenant_code (e.g., 'silvercreek')
  netsuiteParentId: varchar('netsuite_parent_id', { length: 100 }), // NetSuite parent company internal ID
  settings: jsonb('settings').default({}),
  isActive: boolean('is_active').notNull().default(true),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
}, (table) => ({
  tenantIdIndex: index('practices_tenant_id_idx').on(table.tenantId),
}));

// Locations table (for multi-location practices)
export const locations = pgTable('locations', {
  id: uuid('id').primaryKey().defaultRandom(),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  name: varchar('name', { length: 255 }).notNull(),
  address: jsonb('address').notNull(),
  phone: varchar('phone', { length: 20 }),
  email: varchar('email', { length: 255 }),
  externalSystemId: varchar('external_system_id', { length: 100 }), // NetSuite subsidiary ID, ADP location ID, etc.
  externalSystemType: varchar('external_system_type', { length: 50 }), // 'netsuite', 'adp', 'dentrix', etc.
  subsidiaryName: varchar('subsidiary_name', { length: 255 }), // Full subsidiary name from external system (e.g., "SCDP Eastlake, LLC")
  operatingHours: jsonb('operating_hours'), // {monday: {open: '08:00', close: '17:00'}, ...}
  isActive: boolean('is_active').notNull().default(true),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
}, (table) => ({
  externalSystemIndex: index('locations_external_system_idx').on(table.externalSystemId, table.externalSystemType),
}));

// User-Practice relationships (many-to-many)
export const userPractices = pgTable('user_practices', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  role: userRoleEnum('role').notNull(),
  permissions: jsonb('permissions').default([]),
  isActive: boolean('is_active').notNull().default(true),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Integrations table
export const integrations = pgTable('integrations', {
  id: uuid('id').primaryKey().defaultRandom(),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  type: varchar('type', { length: 100 }).notNull(),
  name: varchar('name', { length: 255 }).notNull(),
  status: integrationStatusEnum('status').notNull().default('pending'),
  config: jsonb('config').notNull(), // API credentials, endpoints, etc.
  lastSync: timestamp('last_sync'),
  lastError: text('last_error'),
  isActive: boolean('is_active').notNull().default(true),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const integrationCredentials = pgTable('integration_credentials', {
  id: uuid('id').primaryKey().defaultRandom(),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  integrationType: varchar('integration_type', { length: 100 }).notNull(),
  name: varchar('name', { length: 255 }).notNull(),
  credentials: jsonb('credentials').notNull(),
  metadata: jsonb('metadata').notNull().default({}),
  createdBy: uuid('created_by').references(() => users.id, { onDelete: 'set null' }),
  updatedBy: uuid('updated_by').references(() => users.id, { onDelete: 'set null' }),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
}, (table) => ({
  practiceIntegrationUnique: uniqueIndex('integration_credentials_practice_type_unique').on(table.practiceId, table.integrationType),
  practiceIndex: index('integration_credentials_practice_idx').on(table.practiceId),
}));

// Dashboard templates
export const dashboardTemplates = pgTable('dashboard_templates', {
  id: uuid('id').primaryKey().defaultRandom(),
  name: varchar('name', { length: 255 }).notNull(),
  description: text('description'),
  role: userRoleEnum('role').notNull(),
  layout: jsonb('layout').notNull(), // Grid layout configuration
  widgets: jsonb('widgets').notNull(), // Widget configurations
  isDefault: boolean('is_default').notNull().default(false),
  isActive: boolean('is_active').notNull().default(true),
  createdBy: uuid('created_by').references(() => users.id),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// User dashboard customizations
export const userDashboards = pgTable('user_dashboards', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  templateId: uuid('template_id').references(() => dashboardTemplates.id),
  layout: jsonb('layout').notNull(),
  widgets: jsonb('widgets').notNull(),
  isActive: boolean('is_active').notNull().default(true),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Patients table
export const patients = pgTable('patients', {
  id: uuid('id').primaryKey().defaultRandom(),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  externalId: varchar('external_id', { length: 100 }), // ID from external system (Dentrix, etc.)
  firstName: varchar('first_name', { length: 100 }).notNull(),
  lastName: varchar('last_name', { length: 100 }).notNull(),
  email: varchar('email', { length: 255 }),
  phone: varchar('phone', { length: 20 }),
  dateOfBirth: timestamp('date_of_birth'),
  gender: varchar('gender', { length: 20 }),
  address: jsonb('address'),
  emergencyContact: jsonb('emergency_contact'),
  insurance: jsonb('insurance').default([]),
  medicalHistory: jsonb('medical_history').default({}),
  dentalHistory: jsonb('dental_history').default({}),
  notes: text('notes'),
  status: patientStatusEnum('status').notNull().default('active'),
  lastVisit: timestamp('last_visit'),
  nextAppointment: timestamp('next_appointment'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Appointments table
export const appointments = pgTable('appointments', {
  id: uuid('id').primaryKey().defaultRandom(),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  patientId: uuid('patient_id').notNull().references(() => patients.id, { onDelete: 'cascade' }),
  providerId: uuid('provider_id').notNull().references(() => users.id),
  locationId: uuid('location_id').references(() => locations.id),
  externalId: varchar('external_id', { length: 100 }),
  scheduledStart: timestamp('scheduled_start').notNull(),
  scheduledEnd: timestamp('scheduled_end').notNull(),
  actualStart: timestamp('actual_start'),
  actualEnd: timestamp('actual_end'),
  appointmentType: varchar('appointment_type', { length: 100 }),
  procedures: jsonb('procedures').default([]),
  status: appointmentStatusEnum('status').notNull().default('scheduled'),
  notes: text('notes'),
  checkInTime: timestamp('check_in_time'),
  waitTime: integer('wait_time'), // minutes
  roomNumber: varchar('room_number', { length: 20 }),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Widgets table (for widget metadata and configurations)
export const widgets = pgTable('widgets', {
  id: uuid('id').primaryKey().defaultRandom(),
  name: varchar('name', { length: 255 }).notNull(),
  type: widgetTypeEnum('type').notNull(),
  description: text('description'),
  category: varchar('category', { length: 100 }),
  config: jsonb('config').notNull(), // Widget-specific configuration
  dataSource: varchar('data_source', { length: 100 }).notNull(), // API endpoint or data source
  refreshRate: integer('refresh_rate').default(300), // seconds
  permissions: jsonb('permissions').default([]),
  isActive: boolean('is_active').notNull().default(true),
  version: varchar('version', { length: 20 }).default('1.0.0'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Audit log for security and compliance
export const auditLogs = pgTable('audit_logs', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').references(() => users.id),
  practiceId: uuid('practice_id').references(() => practices.id),
  action: varchar('action', { length: 100 }).notNull(), // CREATE, READ, UPDATE, DELETE
  resource: varchar('resource', { length: 100 }).notNull(), // table/entity name
  resourceId: varchar('resource_id', { length: 100 }),
  details: jsonb('details'), // Additional context
  ipAddress: varchar('ip_address', { length: 45 }),
  userAgent: text('user_agent'),
  timestamp: timestamp('timestamp').notNull().defaultNow(),
});

// System settings and configuration
export const systemSettings = pgTable('system_settings', {
  id: uuid('id').primaryKey().defaultRandom(),
  key: varchar('key', { length: 255 }).notNull().unique(),
  value: jsonb('value').notNull(),
  description: text('description'),
  category: varchar('category', { length: 100 }),
  isPublic: boolean('is_public').notNull().default(false), // Can be accessed by frontend
  updatedBy: uuid('updated_by').references(() => users.id),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const refreshTokens = pgTable('refresh_tokens', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  token: text('token').notNull(),  // Changed to text to accommodate large JWT tokens
  tokenHash: varchar('token_hash', { length: 32 }).unique(),  // MD5 hash for indexing
  expiresAt: timestamp('expires_at').notNull(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const passwordResetTokens = pgTable('password_reset_tokens', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  token: text('token').notNull().unique(),  // Changed to text to accommodate large JWT tokens
  expiresAt: timestamp('expires_at').notNull(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

export const blacklistedTokens = pgTable('blacklisted_tokens', {
  id: uuid('id').primaryKey().defaultRandom(),
  token: text('token').notNull().unique(),  // Changed to text to accommodate large JWT tokens
  expiresAt: timestamp('expires_at').notNull(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// BI Daily Metrics (aggregated, synthetic for demos and fast analytics)
export const biDailyMetrics = pgTable('bi_daily_metrics', {
  id: uuid('id').primaryKey().defaultRandom(),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  locationId: uuid('location_id').references(() => locations.id),
  date: timestamp('date').notNull(),

  // Revenue & patients
  revenue: integer('revenue').default(0),
  targetRevenue: integer('target_revenue').default(0),
  newPatients: integer('new_patients').default(0),
  returningPatients: integer('returning_patients').default(0),

  // Scheduling & operations
  scheduleUtilization: integer('schedule_utilization').default(0), // percentage 0-100
  noShows: integer('no_shows').default(0),
  cancellations: integer('cancellations').default(0),
  avgWaitTime: integer('avg_wait_time').default(0), // minutes

  // Staff & clinical
  staffUtilization: integer('staff_utilization').default(0), // percentage 0-100
  chairUtilization: integer('chair_utilization').default(0), // percentage 0-100
  ontimePerformance: integer('ontime_performance').default(0), // percentage 0-100
  treatmentCompletion: integer('treatment_completion').default(0), // percentage 0-100

  // Financials
  claimsSubmitted: integer('claims_submitted').default(0),
  claimsDenied: integer('claims_denied').default(0),
  collectionsAmount: integer('collections_amount').default(0),
  arCurrent: integer('ar_current').default(0),
  ar30: integer('ar_30').default(0),
  ar60: integer('ar_60').default(0),
  ar90: integer('ar_90').default(0),

  // Benchmarks & forecasting
  benchmarkScore: integer('benchmark_score').default(0), // 0-100
  forecastRevenue: integer('forecast_revenue').default(0),
  forecastPatients: integer('forecast_patients').default(0),

  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});


export const manualIngestionUploads = pgTable('manual_ingestion_uploads', {
  id: uuid('id').primaryKey().defaultRandom(),
  practiceId: uuid('practice_id').notNull().references(() => practices.id, { onDelete: 'cascade' }),
  uploadedBy: uuid('uploaded_by').references(() => users.id, { onDelete: 'set null' }),
  sourceSystem: varchar('source_system', { length: 100 }).notNull(),
  dataset: varchar('dataset', { length: 100 }).default('unknown'),
  originalFilename: varchar('original_filename', { length: 512 }).notNull(),
  storagePath: varchar('storage_path', { length: 1024 }).notNull(),
  status: varchar('status', { length: 50 }).notNull().default('stored'),
  externalLocation: varchar('external_location', { length: 1024 }),
  notes: text('notes'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});


// Relations
export const usersRelations = relations(users, ({ many }) => ({
  userPractices: many(userPractices),
  userDashboards: many(userDashboards),
  appointments: many(appointments),
  auditLogs: many(auditLogs),
}));

export const practicesRelations = relations(practices, ({ many }) => ({
  locations: many(locations),
  userPractices: many(userPractices),
  integrations: many(integrations),
  patients: many(patients),
  appointments: many(appointments),
  manualIngestionUploads: many(manualIngestionUploads),
}));

export const locationsRelations = relations(locations, ({ one, many }) => ({
  practice: one(practices, {
    fields: [locations.practiceId],
    references: [practices.id],
  }),
  appointments: many(appointments),
}));

export const userPracticesRelations = relations(userPractices, ({ one }) => ({
  user: one(users, {
    fields: [userPractices.userId],
    references: [users.id],
  }),
  practice: one(practices, {
    fields: [userPractices.practiceId],
    references: [practices.id],
  }),
}));

export const integrationsRelations = relations(integrations, ({ one }) => ({
  practice: one(practices, {
    fields: [integrations.practiceId],
    references: [practices.id],
  }),
}));

export const dashboardTemplatesRelations = relations(dashboardTemplates, ({ one, many }) => ({
  createdBy: one(users, {
    fields: [dashboardTemplates.createdBy],
    references: [users.id],
  }),
  userDashboards: many(userDashboards),
}));

export const userDashboardsRelations = relations(userDashboards, ({ one }) => ({
  user: one(users, {
    fields: [userDashboards.userId],
    references: [users.id],
  }),
  practice: one(practices, {
    fields: [userDashboards.practiceId],
    references: [practices.id],
  }),
  template: one(dashboardTemplates, {
    fields: [userDashboards.templateId],
    references: [dashboardTemplates.id],
  }),
}));

export const patientsRelations = relations(patients, ({ one, many }) => ({
  practice: one(practices, {
    fields: [patients.practiceId],
    references: [practices.id],
  }),
  appointments: many(appointments),
}));

export const appointmentsRelations = relations(appointments, ({ one }) => ({
  practice: one(practices, {
    fields: [appointments.practiceId],
    references: [practices.id],
  }),
  patient: one(patients, {
    fields: [appointments.patientId],
    references: [patients.id],
  }),
  provider: one(users, {
    fields: [appointments.providerId],
    references: [users.id],
  }),
  location: one(locations, {
    fields: [appointments.locationId],
    references: [locations.id],
  }),
}));


export const auditLogsRelations = relations(auditLogs, ({ one }) => ({
  user: one(users, {
    fields: [auditLogs.userId],
    references: [users.id],
  }),
  practice: one(practices, {
    fields: [auditLogs.practiceId],
    references: [practices.id],
  }),
}));

export const systemSettingsRelations = relations(systemSettings, ({ one }) => ({
  updatedBy: one(users, {
    fields: [systemSettings.updatedBy],
    references: [users.id],
  }),
}));

export const manualIngestionUploadsRelations = relations(manualIngestionUploads, ({ one }) => ({
  practice: one(practices, {
    fields: [manualIngestionUploads.practiceId],
    references: [practices.id],
  }),
  uploadedByUser: one(users, {
    fields: [manualIngestionUploads.uploadedBy],
    references: [users.id],
  }),
}));

// Type definitions for TypeScript
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Practice = typeof practices.$inferSelect;
export type NewPractice = typeof practices.$inferInsert;
export type Location = typeof locations.$inferSelect;
export type NewLocation = typeof locations.$inferInsert;
export type UserPractice = typeof userPractices.$inferSelect;
export type NewUserPractice = typeof userPractices.$inferInsert;
export type Integration = typeof integrations.$inferSelect;
export type NewIntegration = typeof integrations.$inferInsert;
export type DashboardTemplate = typeof dashboardTemplates.$inferSelect;
export type NewDashboardTemplate = typeof dashboardTemplates.$inferInsert;
export type UserDashboard = typeof userDashboards.$inferSelect;
export type NewUserDashboard = typeof userDashboards.$inferInsert;
export type Patient = typeof patients.$inferSelect;
export type NewPatient = typeof patients.$inferInsert;
export type Appointment = typeof appointments.$inferSelect;
export type NewAppointment = typeof appointments.$inferInsert;
export type Widget = typeof widgets.$inferSelect;
export type NewWidget = typeof widgets.$inferInsert;
export type AuditLog = typeof auditLogs.$inferSelect;
export type NewAuditLog = typeof auditLogs.$inferInsert;
export type SystemSetting = typeof systemSettings.$inferSelect;
export type NewSystemSetting = typeof systemSettings.$inferInsert;
export type ManualIngestionUpload = typeof manualIngestionUploads.$inferSelect;
export type NewManualIngestionUpload = typeof manualIngestionUploads.$inferInsert;

// Enums for TypeScript
export type UserRole = 'admin' | 'executive' | 'manager' | 'clinician' | 'staff';
export type IntegrationType = string;
export type IntegrationStatus = 'connected' | 'disconnected' | 'error' | 'pending';
export type AppointmentStatus = 'scheduled' | 'confirmed' | 'checked_in' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';
export type PatientStatus = 'active' | 'inactive' | 'archived';
export type WidgetType = 'metric' | 'chart' | 'list' | 'action';
