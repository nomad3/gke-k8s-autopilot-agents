# Navigation System

## Overview
The navigation system provides intuitive, role-based navigation throughout the dental ERP platform. It features a collapsible sidebar, unified search, and contextual menus that adapt based on user roles and current workflows.

## Design Specifications

### Sidebar Navigation

#### Visual Properties
- **Width (Expanded)**: 280px (layout.sidebar.expanded)
- **Width (Collapsed)**: 80px (layout.sidebar.collapsed)
- **Background**: Linear gradient from #f8fafc to #f1f5f9
- **Border**: 1px solid #e2e8f0 (right border)
- **Box Shadow**: 2px 0 8px rgba(0, 0, 0, 0.04)

#### Layout Structure
```html
<nav class="sidebar" role="navigation" aria-label="Main navigation">
  <div class="sidebar-header">
    <div class="logo">
      <img src="/logo.svg" alt="Dental ERP" />
      <span class="logo-text">Dental ERP</span>
    </div>
    <button class="collapse-toggle" aria-label="Toggle navigation">
      <!-- Collapse icon -->
    </button>
  </div>

  <div class="sidebar-search">
    <div class="search-container">
      <input type="search" placeholder="Search across systems..." />
      <button class="search-button">
        <!-- Search icon -->
      </button>
    </div>
  </div>

  <div class="sidebar-content">
    <div class="nav-section">
      <h4 class="nav-section-title">Dashboard</h4>
      <ul class="nav-items">
        <!-- Navigation items -->
      </ul>
    </div>
  </div>

  <div class="sidebar-footer">
    <div class="user-profile">
      <!-- User info and settings -->
    </div>
  </div>
</nav>
```

### Navigation Items

#### Primary Navigation Item
```html
<li class="nav-item">
  <a href="/dashboard" class="nav-link" aria-current="page">
    <span class="nav-icon">
      <!-- Dashboard icon -->
    </span>
    <span class="nav-label">Dashboard</span>
    <span class="nav-badge">3</span>
  </a>
</li>
```

#### Navigation with Submenu
```html
<li class="nav-item has-submenu">
  <button class="nav-link" aria-expanded="false">
    <span class="nav-icon">
      <!-- Patients icon -->
    </span>
    <span class="nav-label">Patients</span>
    <span class="nav-arrow">
      <!-- Chevron icon -->
    </span>
  </button>
  <ul class="nav-submenu" aria-hidden="true">
    <li><a href="/patients/active" class="nav-sublink">Active Patients</a></li>
    <li><a href="/patients/new" class="nav-sublink">New Patients</a></li>
    <li><a href="/patients/inactive" class="nav-sublink">Inactive Patients</a></li>
  </ul>
</li>
```

### States

#### Default Navigation Link
```css
.nav-link {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin: 2px 8px;
  border-radius: 8px;
  color: #475569;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.15s ease;
}
```

#### Hover State
```css
.nav-link:hover {
  background: #e2e8f0;
  color: #334155;
  transform: translateX(2px);
}
```

#### Active State
```css
.nav-link[aria-current="page"] {
  background: linear-gradient(135deg, #0ea5e9, #06b6d4);
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(14, 165, 233, 0.3);
}
```

#### Focus State
```css
.nav-link:focus {
  outline: 2px solid #0ea5e9;
  outline-offset: 2px;
  background: #e0f2fe;
}
```

### Role-Based Navigation

#### Executive View
```javascript
const executiveNavigation = [
  {
    section: "Overview",
    items: [
      { label: "Executive Dashboard", icon: "dashboard", href: "/executive" },
      { label: "Performance Analytics", icon: "chart-bar", href: "/analytics" },
      { label: "Financial Reports", icon: "currency-dollar", href: "/reports/financial" }
    ]
  },
  {
    section: "Operations",
    items: [
      { label: "Multi-Location View", icon: "building-office", href: "/locations" },
      { label: "Staff Overview", icon: "users", href: "/staff" },
      { label: "Market Intelligence", icon: "chart-line", href: "/market" }
    ]
  }
];
```

#### Practice Manager View
```javascript
const managerNavigation = [
  {
    section: "Daily Operations",
    items: [
      { label: "Manager Dashboard", icon: "dashboard", href: "/manager" },
      { label: "Schedule Management", icon: "calendar", href: "/schedule" },
      { label: "Patient Management", icon: "user-group", href: "/patients" }
    ]
  },
  {
    section: "Staff & Resources",
    items: [
      { label: "Staff Management", icon: "users", href: "/staff" },
      { label: "Resource Planning", icon: "clipboard-list", href: "/resources" },
      { label: "Performance Tracking", icon: "chart-bar", href: "/performance" }
    ]
  }
];
```

#### Clinician View
```javascript
const clinicianNavigation = [
  {
    section: "Patient Care",
    items: [
      { label: "Clinical Dashboard", icon: "dashboard", href: "/clinical" },
      { label: "Today's Schedule", icon: "calendar-days", href: "/schedule/today" },
      { label: "Patient Charts", icon: "document-text", href: "/charts" }
    ]
  },
  {
    section: "Treatment",
    items: [
      { label: "Treatment Plans", icon: "clipboard-check", href: "/treatment-plans" },
      { label: "Clinical Notes", icon: "pencil-square", href: "/notes" },
      { label: "Imaging", icon: "photo", href: "/imaging" }
    ]
  }
];
```

### Top Navigation Bar

#### Structure
```html
<header class="top-nav" role="banner">
  <div class="top-nav-content">
    <div class="breadcrumb-container">
      <nav aria-label="Breadcrumb">
        <ol class="breadcrumb">
          <li><a href="/dashboard">Dashboard</a></li>
          <li><a href="/patients">Patients</a></li>
          <li aria-current="page">John Doe</li>
        </ol>
      </nav>
    </div>

    <div class="top-nav-actions">
      <button class="notification-button" aria-label="Notifications">
        <span class="notification-icon"></span>
        <span class="notification-count">3</span>
      </button>

      <div class="user-menu">
        <button class="user-button" aria-expanded="false">
          <img src="/avatar.jpg" alt="User avatar" class="avatar" />
          <span class="user-name">Dr. Smith</span>
        </button>
        <div class="user-dropdown" aria-hidden="true">
          <!-- User menu items -->
        </div>
      </div>
    </div>
  </div>
</header>
```

### Unified Search

#### Search Component
```html
<div class="unified-search">
  <div class="search-input-container">
    <input
      type="search"
      placeholder="Search patients, appointments, notes..."
      class="search-input"
      aria-label="Search across all systems"
      autocomplete="off"
    />
    <div class="search-filters">
      <button class="filter-button" aria-label="Filter by system">
        <span>All Systems</span>
        <!-- Dropdown icon -->
      </button>
    </div>
  </div>

  <div class="search-results" aria-hidden="true">
    <div class="search-section">
      <h5 class="search-section-title">Patients</h5>
      <ul class="search-items">
        <!-- Search result items -->
      </ul>
    </div>
  </div>
</div>
```

#### Search Results Structure
```html
<li class="search-item">
  <div class="search-item-content">
    <div class="search-item-icon">
      <span class="system-badge dentrix">D</span>
    </div>
    <div class="search-item-details">
      <div class="search-item-title">John Doe</div>
      <div class="search-item-subtitle">Patient • Last visit: 2023-09-15</div>
      <div class="search-item-path">Dentrix > Patients > Active</div>
    </div>
  </div>
</li>
```

### Responsive Navigation

#### Mobile Navigation (< 768px)
- Sidebar becomes full-screen overlay
- Top navigation shows hamburger menu
- Search becomes modal interface
- Touch-friendly tap targets (44px minimum)

#### Tablet Navigation (768px - 1199px)
- Sidebar auto-collapses to save space
- Navigation items show tooltips when collapsed
- Search remains inline but with simplified filters

#### Desktop Navigation (1200px+)
- Full expanded sidebar by default
- All navigation features available
- Keyboard shortcuts enabled

### System Integration Indicators

#### Integration Status
```html
<div class="integration-status">
  <div class="system-indicator dentrix connected" title="Dentrix - Connected">
    <span class="system-icon">D</span>
    <span class="status-dot"></span>
  </div>
  <div class="system-indicator dentalintel connected" title="DentalIntel - Connected">
    <span class="system-icon">DI</span>
    <span class="status-dot"></span>
  </div>
  <div class="system-indicator adp warning" title="ADP - Limited Access">
    <span class="system-icon">A</span>
    <span class="status-dot"></span>
  </div>
  <div class="system-indicator eaglesoft connected" title="Eaglesoft - Connected">
    <span class="system-icon">E</span>
    <span class="status-dot"></span>
  </div>
</div>
```

### Accessibility Features

#### Keyboard Navigation
- Tab/Shift+Tab: Navigate through items
- Enter/Space: Activate links and buttons
- Arrow keys: Navigate within menus
- Escape: Close open menus/dropdowns

#### Screen Reader Support
- Proper ARIA labels and roles
- Live regions for dynamic content
- Clear focus indicators
- Descriptive link text

#### Focus Management
```css
.nav-link:focus,
.search-input:focus,
.user-button:focus {
  outline: 2px solid #0ea5e9;
  outline-offset: 2px;
  position: relative;
  z-index: 10;
}
```

### Animation & Transitions

#### Sidebar Collapse Animation
```css
.sidebar {
  width: 280px;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar.collapsed {
  width: 80px;
}

.nav-label,
.logo-text {
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar.collapsed .nav-label,
.sidebar.collapsed .logo-text {
  opacity: 0;
}
```

#### Menu Animations
```css
.nav-submenu {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease-out;
}

.nav-item.expanded .nav-submenu {
  max-height: 200px;
}
```

### Performance Considerations
- Lazy load navigation icons
- Debounce search input (300ms delay)
- Virtual scrolling for large result sets
- Cache frequently accessed routes
- Preload critical navigation targets
