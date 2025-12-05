# Dental Practice Rollup Mini ERP - Technical Specification

## Executive Summary

This technical specification provides comprehensive implementation guidelines for the Dental Practice Rollup Mini ERP system (`dentalERP`). The platform delivers role-based dashboards, real-time analytics, and WCAG 2.1 AA accessibility compliance while ingesting data from external practice systems (Dentrix, Eaglesoft, DentalIntel, ADP, NetSuite, QuickBooks) through modular REST connectors orchestrated by MCP workflows and processed via the integration queue/back-end services defined in this repository.

## System Architecture

### Technology Stack

#### Frontend
```json
{
  "framework": "React 18.x",
  "typescript": "5.x",
  "bundler": "Vite",
  "styling": "Tailwind CSS + CSS Modules",
  "state_management": "Zustand + React Query",
  "testing": "Vitest + Testing Library",
  "accessibility": "@axe-core/react"
}
```

#### Backend
```json
{
  "runtime": "Node.js 20.x",
  "framework": "Express.js",
  "database": "PostgreSQL 15.x (Drizzle ORM)",
  "auth": "JWT (custom implementation) with DB-backed refresh/password-reset tokens",
  "queue": "Integration queue persisted in PostgreSQL with advisory locking",
  "api": "REST JSON",
  "workflows": "MCP (integration sync)",
  "logging": "Winston"
}
```

#### Infrastructure
```json
{
  "cloud": "Google Cloud Platform (Compute Engine VM)",
  "containers": "Docker Compose (frontend, backend, MCP, Postgres, Redis)",
  "workflows": "MCP Server + Worker containers",
  "monitoring": "MCP UI + application logs",
  "ci_cd": "GitHub Actions (build/test) + manual deploy",
  "security": "TLS termination via reverse proxy, secrets via env vars"
}
```

## Integration Specifications

- **MCP Workflows**: `backend/src/workflows/integrationSyncWorkflow.ts` orchestrates data pulls via activities defined in `backend/src/workflows/activities/`. Workflows target the `integration-sync` task queue served by `backend/src/workers/integrationWorker.ts`.
- **Integration Connectors**: Vendor-specific HTTP clients live under `backend/src/integrations/`. Each module exports `fetch<Vendor>Data()` implementing authentication and dataset-specific fetching. Current status:
  - `netsuite/`: Token-Based Auth (TBA) support with endpoints for general ledger, transactions, subsidiaries.
  - `adp/`, `dentalintel/`, `dentrix/`, `eaglesoft/`, `quickbooks/`: scaffolding in place; implementations pending API credentials.
- **Queue Orchestration**: `IntegrationQueueService` (`backend/src/services/ingestionQueue.ts`) persists job requests in Postgres (`integration_queue_jobs`) and drives ingestion via `IngestionService`, using row-level locking to manage workers and retries.
- **Authentication Tokens**: Refresh, password-reset, and blacklist tokens are stored in Postgres tables (`refresh_tokens`, `password_reset_tokens`, `blacklisted_tokens`), removing the need for Redis while maintaining auditability and HIPAA controls.
- **Manual Ingestion**: `documentation/manual-ingestion.md` details CSV/PDF uploads processed by `backend/src/routes/integrations.ts` and stored through `IngestionService`.
- **Data Landing**: Raw API responses are serialized to JSON and written to `uploads/` (VM storage) with metadata recorded in Postgres tables defined in `backend/src/database/schema.ts`. Future state will sync these artifacts to GCS per `documentation/data-integration-spec.md`.

## Data Models

### Core Entities
```typescript
interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  practiceId: string;
  permissions: Permission[];
  preferences: UserPreferences;
  lastLogin: Date;
  createdAt: Date;
  updatedAt: Date;
}

interface Patient {
  id: string;
  practiceId: string;
  firstName: string;
  lastName: string;
  dateOfBirth: Date;
  phone: string;
  email?: string;
  address: Address;
  insurance: InsuranceInfo[];
  medicalHistory: MedicalHistory;
  dentalHistory: DentalHistory;
  appointments: Appointment[];
  treatmentPlans: TreatmentPlan[];
  lastVisit?: Date;
  nextAppointment?: Date;
  status: PatientStatus;
  createdAt: Date;
  updatedAt: Date;
}

interface Appointment {
  id: string;
  patientId: string;
  providerId: string;
  practiceId: string;
  roomId?: string;
  scheduledStart: Date;
  scheduledEnd: Date;
  actualStart?: Date;
  actualEnd?: Date;
  appointmentType: AppointmentType;
  status: AppointmentStatus;
  procedures: Procedure[];
  notes?: string;
  checkInTime?: Date;
  waitTime?: number;
  createdAt: Date;
  updatedAt: Date;
}

interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  position: WidgetPosition;
  size: WidgetSize;
  config: WidgetConfig;
  dataSource: DataSource;
  refreshRate: number;
  permissions: Permission[];
  isVisible: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

## API Design

### GraphQL Schema
```graphql
type Query {
  # User & Authentication
  me: User!

  # Dashboard
  dashboard(role: UserRole!): Dashboard!
  widgets(dashboardId: ID!): [Widget!]!

  # Patients
  patients(
    practiceId: ID!
    search: String
    status: PatientStatus
    limit: Int = 20
    offset: Int = 0
  ): PatientsConnection!

  patient(id: ID!): Patient!

  # Appointments
  appointments(
    practiceId: ID!
    date: Date!
    providerId: ID
  ): [Appointment!]!

  # Analytics
  practiceMetrics(
    practiceId: ID!
    dateRange: DateRangeInput!
    metrics: [MetricType!]!
  ): PracticeMetrics!
}

type Mutation {
  # Dashboard Management
  updateWidgetPosition(
    widgetId: ID!
    position: WidgetPositionInput!
  ): Widget!

  updateWidgetConfig(
    widgetId: ID!
    config: WidgetConfigInput!
  ): Widget!

  # Appointment Management
  createAppointment(input: AppointmentInput!): Appointment!
  updateAppointment(id: ID!, input: AppointmentUpdateInput!): Appointment!
  checkInPatient(appointmentId: ID!): Appointment!

  # Patient Management
  createPatient(input: PatientInput!): Patient!
  updatePatient(id: ID!, input: PatientUpdateInput!): Patient!
}

type Subscription {
  appointmentUpdates(practiceId: ID!): Appointment!
  patientCheckIns(practiceId: ID!): PatientCheckIn!
  systemAlerts(practiceId: ID!): SystemAlert!
}
```

### REST API Endpoints
```typescript
// Authentication
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/logout

// Dashboard
GET    /api/dashboard/{role}
PUT    /api/dashboard/layout
GET    /api/widgets/{widgetId}/data

// Patients
GET    /api/patients
POST   /api/patients
GET    /api/patients/{id}
PUT    /api/patients/{id}
GET    /api/patients/{id}/appointments
GET    /api/patients/{id}/treatments

// Appointments
GET    /api/appointments
POST   /api/appointments
PUT    /api/appointments/{id}
POST   /api/appointments/{id}/checkin
GET    /api/appointments/conflicts

// Analytics
GET    /api/analytics/practice-metrics
GET    /api/analytics/staff-performance
GET    /api/analytics/revenue-trends
GET    /api/analytics/patient-satisfaction

// Integration Health
GET    /api/integrations/status
POST   /api/integrations/{system}/sync
GET    /api/integrations/{system}/logs
```

## Security Implementation

### Authentication & Authorization
```typescript
interface AuthConfig {
  jwtSecret: string;
  tokenExpiration: string;
  refreshTokenExpiration: string;
  passwordPolicy: PasswordPolicy;
  mfaRequired: boolean;
  maxLoginAttempts: number;
  lockoutDuration: number;
}

interface Permission {
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete';
  conditions?: PermissionConditions;
}

// Role-based permissions
const rolePermissions: Record<UserRole, Permission[]> = {
  executive: [
    { resource: 'dashboard', action: 'read' },
    { resource: 'analytics', action: 'read' },
    { resource: 'reports', action: 'read' },
    { resource: 'staff', action: 'read' }
  ],
  manager: [
    { resource: 'dashboard', action: 'read' },
    { resource: 'patients', action: 'read' },
    { resource: 'appointments', action: 'create' },
    { resource: 'appointments', action: 'update' },
    { resource: 'staff', action: 'read' },
    { resource: 'schedule', action: 'update' }
  ],
  clinician: [
    { resource: 'dashboard', action: 'read' },
    { resource: 'patients', action: 'read' },
    { resource: 'patients', action: 'update', conditions: { ownPatientsOnly: true } },
    { resource: 'appointments', action: 'read' },
    { resource: 'treatments', action: 'update' }
  ]
};
```

### Data Protection
```typescript
interface EncryptionConfig {
  algorithm: 'AES-256-GCM';
  keyRotationPeriod: number;
  fieldLevelEncryption: string[];
  auditLogging: boolean;
}

// HIPAA Compliance
const hipaaFields = [
  'patient.ssn',
  'patient.medicalHistory',
  'patient.dentalHistory',
  'appointment.notes',
  'treatment.notes'
];

// Data masking for different roles
const dataMasking: Record<UserRole, string[]> = {
  executive: ['patient.ssn', 'patient.medicalHistory'],
  manager: ['patient.ssn'],
  clinician: [] // Full access to assigned patients
};
```

## Performance Requirements

### Response Times
```typescript
interface PerformanceTargets {
  dashboardLoad: number;        // < 2 seconds
  widgetRefresh: number;        // < 500ms
  searchResults: number;        // < 300ms
  appointmentBooking: number;   // < 1 second
  patientLookup: number;       // < 200ms
  reportGeneration: number;     // < 5 seconds
}
```

### Scalability
```typescript
interface ScalabilityRequirements {
  concurrentUsers: number;      // 500+ simultaneous users
  practicesSupported: number;   // 100+ practice locations
  dailyAppointments: number;    // 10,000+ appointments/day
  dataRetention: string;        // 7 years minimum
  backupFrequency: string;      // Every 4 hours
  rto: number;                  // Recovery Time Objective: 4 hours
  rpo: number;                  // Recovery Point Objective: 1 hour
}
```

## Monitoring & Analytics

### Application Monitoring
```typescript
interface MonitoringConfig {
  healthChecks: string[];
  alertThresholds: AlertThresholds;
  metrics: MetricCollection[];
  dashboards: MonitoringDashboard[];
}

interface AlertThresholds {
  responseTime95th: number;     // 2000ms
  errorRate: number;            // 1%
  cpuUtilization: number;       // 80%
  memoryUtilization: number;    // 85%
  diskUtilization: number;      // 90%
  integrationFailureRate: number; // 5%
}
```

### User Analytics
```typescript
interface UserAnalytics {
  pageViews: PageViewEvent[];
  userSessions: SessionEvent[];
  featureUsage: FeatureUsageEvent[];
  errorEvents: ErrorEvent[];
  performanceEvents: PerformanceEvent[];
}

// Privacy-compliant analytics
interface AnalyticsConfig {
  anonymizeIPs: boolean;
  respectDoNotTrack: boolean;
  gdprCompliant: boolean;
  hipaaCompliant: boolean;
  dataRetentionDays: number;
}
```

## Deployment Strategy

### Development Workflow
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
      - name: Accessibility tests
        run: npm run test:a11y
      - name: Security scan
        run: npm audit

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build application
        run: npm run build
      - name: Build Docker image
        run: docker build -t dental-erp:${{ github.sha }} .

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [test, build]
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: ./scripts/deploy-staging.sh
      - name: Run integration tests
        run: npm run test:integration
      - name: Deploy to production
        run: ./scripts/deploy-production.sh
```

### Environment Configuration
```typescript
interface EnvironmentConfig {
  development: {
    database: 'postgresql://localhost:5432/dental_erp_dev';
    redis: 'redis://localhost:6379';
    integrations: {
      dentrix: { endpoint: 'https://dentrix-dev.local', apiKey: 'dev_key' };
      dentalintel: { endpoint: 'https://di-dev.local', apiKey: 'dev_key' };
      adp: { endpoint: 'https://adp-sandbox.com', apiKey: 'dev_key' };
      eaglesoft: { endpoint: 'https://es-dev.local', apiKey: 'dev_key' };
    };
    features: {
      debugMode: true;
      mockIntegrations: true;
    };
  };

  production: {
    database: process.env.DATABASE_URL;
    redis: process.env.REDIS_URL;
    integrations: {
      dentrix: { endpoint: process.env.DENTRIX_ENDPOINT, apiKey: process.env.DENTRIX_API_KEY };
      dentalintel: { endpoint: process.env.DI_ENDPOINT, apiKey: process.env.DI_API_KEY };
      adp: { endpoint: process.env.ADP_ENDPOINT, apiKey: process.env.ADP_API_KEY };
      eaglesoft: { endpoint: process.env.ES_ENDPOINT, apiKey: process.env.ES_API_KEY };
    };
    features: {
      debugMode: false;
      mockIntegrations: false;
    };
  };
}
```

## Testing Strategy

### Testing Pyramid
```typescript
// Unit Tests (70%)
describe('Dashboard Widget', () => {
  it('renders metric widget correctly', () => {
    const widget = render(<MetricWidget data={mockData} />);
    expect(widget.getByText('$2.4M')).toBeInTheDocument();
  });
});

// Integration Tests (20%)
describe('Patient API Integration', () => {
  it('fetches patient data from Dentrix', async () => {
    const patients = await patientService.getPatients();
    expect(patients).toHaveLength(10);
  });
});

// E2E Tests (10%)
describe('Appointment Booking Flow', () => {
  it('allows manager to book appointment', async () => {
    await page.goto('/appointments');
    await page.click('[data-testid="new-appointment"]');
    await page.fill('[data-testid="patient-search"]', 'John Doe');
    // ... rest of flow
  });
});
```

### Accessibility Testing
```typescript
// Automated accessibility tests
describe('Accessibility Compliance', () => {
  it('meets WCAG 2.1 AA standards', async () => {
    const { container } = render(<Dashboard />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('supports keyboard navigation', async () => {
    render(<Dashboard />);
    const firstButton = screen.getAllByRole('button')[0];
    firstButton.focus();
    fireEvent.keyDown(firstButton, { key: 'Tab' });
    // Verify focus moved to next interactive element
  });
});
```

## Maintenance & Support

### Update Procedures
```typescript
interface UpdateProcedure {
  preDeployment: string[];
  deployment: string[];
  postDeployment: string[];
  rollback: string[];
}

const updateSteps: UpdateProcedure = {
  preDeployment: [
    'Notify users of maintenance window',
    'Create database backup',
    'Run pre-migration scripts',
    'Verify integration health'
  ],
  deployment: [
    'Deploy to staging environment',
    'Run automated test suite',
    'Deploy to production',
    'Monitor system health'
  ],
  postDeployment: [
    'Verify all integrations',
    'Check dashboard functionality',
    'Monitor error rates',
    'Notify users of completion'
  ],
  rollback: [
    'Stop new deployments',
    'Restore previous version',
    'Restore database backup',
    'Verify system stability'
  ]
};
```

### Support Tiers
```typescript
interface SupportTier {
  name: string;
  responseTime: string;
  availabilityHours: string;
  channels: string[];
  escalationPath: string[];
}

const supportTiers: SupportTier[] = [
  {
    name: 'Critical',
    responseTime: '15 minutes',
    availabilityHours: '24/7',
    channels: ['phone', 'email', 'chat'],
    escalationPath: ['L1 Support', 'L2 Engineering', 'Senior Engineering', 'CTO']
  },
  {
    name: 'High',
    responseTime: '2 hours',
    availabilityHours: 'Business hours',
    channels: ['email', 'chat'],
    escalationPath: ['L1 Support', 'L2 Engineering']
  },
  {
    name: 'Medium',
    responseTime: '24 hours',
    availabilityHours: 'Business hours',
    channels: ['email'],
    escalationPath: ['L1 Support']
  }
];
```

This technical specification provides development teams with comprehensive implementation guidelines while ensuring system reliability, security, and maintainability for the dental practice management ecosystem.
