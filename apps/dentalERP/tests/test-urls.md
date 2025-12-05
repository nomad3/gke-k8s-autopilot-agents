# Dental Practice ERP - URL Testing Guide

## 🚀 Quick Start Testing

After running `docker-compose up`, test these main URLs:

### Core Application URLs

#### 1. Frontend Application
**URL**: http://localhost:3000
- **What to expect**: Login page with professional healthcare styling
- **Design**: Matches AuthLayout from wireframes with gradient background
- **Features**: Clean login form, responsive design, healthcare branding

#### 2. Backend API Health Check
**URL**: http://localhost:3001/health
- **What to expect**: JSON health status with service connections
- **Response format**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-27T...",
  "services": {
    "database": "connected",
    "redis": "connected"
  },
  "version": "1.0.0",
  "environment": "development"
}
```

#### 3. API Documentation
**URL**: http://localhost:3001/api-docs
- **What to expect**: Swagger/OpenAPI documentation (when implemented)
- **Features**: Interactive API testing, endpoint documentation

### Dashboard URLs (After Login Implementation)

Based on our comprehensive wireframes, these will be the main dashboard URLs:

#### Executive Dashboard
**URL**: http://localhost:3000/dashboard (with executive role)
- **Features**: Strategic KPI overview, multi-location analytics
- **Widgets**: Revenue trends, location performance matrix
- **Layout**: 12-column grid with 4 KPI widgets + 2x2 chart widgets

#### Practice Manager Dashboard
**URL**: http://localhost:3000/dashboard (with manager role)
- **Features**: Daily operations, staff coordination, patient flow
- **Widgets**: Today's overview, schedule timeline, patient queue
- **Real-time**: 30-second refresh for patient queue, live conflicts

#### Clinician Dashboard
**URL**: http://localhost:3000/dashboard (with clinician role)
- **Features**: Patient care focus, treatment tracking
- **Integration**: Direct Dentrix charts, Eaglesoft billing access

### Application Sections

#### Patient Management
**URL**: http://localhost:3000/patients
- **Access**: Manager, Clinician roles
- **Features**: Patient search, records, treatment history

#### Appointment Scheduling
**URL**: http://localhost:3000/appointments
- **Access**: Manager, Clinician roles
- **Features**: Calendar view, conflict detection, real-time updates

#### Practice Management
**URL**: http://localhost:3000/practices
- **Access**: Admin, Executive, Manager roles
- **Features**: Multi-location management, settings

#### System Integrations
**URL**: http://localhost:3000/integrations
- **Access**: Admin, Executive, Manager roles
- **Features**: Dentrix, DentalIntel, ADP, Eaglesoft status

## 🧪 Testing Checklist

### Database Services
- [ ] PostgreSQL running on port 5432
- [ ] Redis running on port 6379
- [ ] Health check returns "connected" for both services

### Frontend Testing
- [ ] Login page loads with healthcare styling
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Navigation follows wireframe specifications
- [ ] Color palette matches design system tokens
- [ ] Typography uses Inter font family as specified

### Backend API Testing
- [ ] Health endpoint returns proper JSON
- [ ] CORS headers allow frontend access
- [ ] Security headers present (Helmet.js)
- [ ] Rate limiting works (100 requests per 15 minutes)

### Design System Validation
- [ ] Colors match healthcare palette from `/design-system/tokens/colors.json`
- [ ] Spacing follows the token system from `/design-system/tokens/spacing.json`
- [ ] Typography implements Inter + Lexend from `/design-system/tokens/typography.json`
- [ ] Components follow specifications from `/design-system/components/`

### Wireframe Compliance
- [ ] Dashboard layout matches `/wireframes/executive-dashboard/layout.md`
- [ ] Navigation follows `/design-system/components/navigation.md`
- [ ] Widget system ready for `/design-system/components/dashboard-widget.md`

## 🔧 Manual Testing Commands

### Test Database Connection
```bash
docker exec -it dentalerp-postgres-1 psql -U postgres -d dental_erp_dev -c "SELECT version();"
```

### Test Redis Connection
```bash
docker exec -it dentalerp-redis-1 redis-cli ping
```

### Test API Health
```bash
curl -s http://localhost:3001/health | jq
```

### Test CORS Headers
```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -v http://localhost:3001/health
```

## 🎯 Expected Behavior

### On First Visit
1. **Frontend (localhost:3000)**: Redirects to `/auth/login`
2. **Login Page**: Professional healthcare styling with gradient background
3. **No Authentication**: Shows login form (no dashboard access)

### With Mock Authentication
1. **Dashboard Access**: Role-based dashboard layout
2. **Navigation**: Sidebar with healthcare-appropriate icons
3. **Widgets**: Placeholder data matching wireframe specifications
4. **Responsive**: Mobile-first design from our specifications

### Integration Status
1. **System Indicators**: Shows Dentrix, DentalIntel, ADP, Eaglesoft status
2. **Mock Mode**: All integrations show "Connected" in development
3. **Real-time Updates**: WebSocket connection for live data (when implemented)

This testing guide is based on our comprehensive design system, wireframes, and technical specifications established in the previous commits.
