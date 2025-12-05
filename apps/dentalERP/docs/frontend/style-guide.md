# Dental ERP Design System - Style Guide

## Overview
This style guide provides comprehensive specifications for the visual design language of the Dental Practice Rollup Mini ERP system, ensuring consistency across all interfaces and user touchpoints.

## Brand Identity

### Design Principles
1. **Clinical Precision**: Clean, organized layouts that reflect the precision required in dental care
2. **Professional Trust**: Conservative color palette that instills confidence and reliability
3. **Operational Efficiency**: Streamlined interfaces that reduce cognitive load for busy practitioners
4. **Accessibility First**: Inclusive design that works for all users and assistive technologies
5. **Integration Harmony**: Unified visual language across disparate systems

### Voice & Tone
- **Professional yet approachable**: Medical authority without intimidation
- **Clear and direct**: Precise communication without jargon
- **Supportive and confident**: Empowering users to make informed decisions
- **Efficient and focused**: Respects the time constraints of healthcare professionals

## Color System

### Primary Palette
```css
:root {
  /* Primary Blue - Trust, Professional, Medical */
  --color-primary-50: #f0f9ff;
  --color-primary-100: #e0f2fe;
  --color-primary-200: #bae6fd;
  --color-primary-300: #7dd3fc;
  --color-primary-400: #38bdf8;
  --color-primary-500: #0ea5e9;  /* Primary brand color */
  --color-primary-600: #0284c7;
  --color-primary-700: #0369a1;
  --color-primary-800: #075985;
  --color-primary-900: #0c4a6e;
}
```

### Healthcare Semantic Colors
```css
:root {
  /* Dental-specific color associations */
  --color-dental: #00a8cc;        /* Clean, sterile blue */
  --color-medical: #0066cc;       /* Traditional medical blue */
  --color-wellness: #4ade80;      /* Health, growth green */
  --color-emergency: #ef4444;     /* Alert, urgent red */
  --color-appointment: #8b5cf6;   /* Scheduling purple */
  --color-treatment: #06b6d4;     /* Treatment cyan */
  --color-revenue: #10b981;       /* Financial success green */
  --color-patient: #3b82f6;       /* Patient care blue */
}
```

### Status & Feedback Colors
```css
:root {
  /* Success States */
  --color-success-50: #f0fdf4;
  --color-success-500: #22c55e;
  --color-success-700: #15803d;

  /* Warning States */
  --color-warning-50: #fffbeb;
  --color-warning-500: #f59e0b;
  --color-warning-700: #b45309;

  /* Error States */
  --color-error-50: #fef2f2;
  --color-error-500: #ef4444;
  --color-error-700: #b91c1c;

  /* Information States */
  --color-info-50: #eff6ff;
  --color-info-500: #3b82f6;
  --color-info-700: #1d4ed8;
}
```

### Usage Guidelines

#### Primary Color Applications
- **Buttons**: Primary actions, navigation active states
- **Links**: Interactive text elements, breadcrumbs
- **Focus States**: Form inputs, keyboard navigation
- **Branding**: Logo, headers, key UI elements

#### Color Accessibility
- Minimum contrast ratio: 4.5:1 for normal text
- Minimum contrast ratio: 3:1 for large text (18px+ or 14px+ bold)
- Color should never be the only means of conveying information
- All interactive elements must have focus indicators

## Typography

### Font Families
```css
:root {
  /* Primary font for UI and body text */
  --font-family-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                         Roboto, sans-serif;

  /* Display font for headings and emphasis */
  --font-family-display: 'Lexend', 'Inter', -apple-system, BlinkMacSystemFont,
                         'Segoe UI', Roboto, sans-serif;

  /* Monospace for code and data */
  --font-family-mono: 'JetBrains Mono', 'Fira Code', Consolas,
                      'Liberation Mono', Menlo, monospace;
}
```

### Type Scale
```css
:root {
  --text-xs: 0.75rem;    /* 12px - captions, labels */
  --text-sm: 0.875rem;   /* 14px - body small, nav items */
  --text-base: 1rem;     /* 16px - body text, buttons */
  --text-lg: 1.125rem;   /* 18px - body large, subheadings */
  --text-xl: 1.25rem;    /* 20px - headings level 4 */
  --text-2xl: 1.5rem;    /* 24px - headings level 3 */
  --text-3xl: 1.875rem;  /* 30px - headings level 2 */
  --text-4xl: 2.25rem;   /* 36px - headings level 1 */
  --text-5xl: 3rem;      /* 48px - display headings */
}
```

### Text Styles

#### Headings
```css
.heading-1 {
  font-family: var(--font-family-display);
  font-size: var(--text-4xl);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.025em;
  color: var(--color-gray-900);
}

.heading-2 {
  font-family: var(--font-family-display);
  font-size: var(--text-3xl);
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.025em;
  color: var(--color-gray-900);
}

.heading-3 {
  font-family: var(--font-family-primary);
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.25;
  color: var(--color-gray-900);
}

.heading-4 {
  font-family: var(--font-family-primary);
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1.375;
  color: var(--color-gray-900);
}
```

#### Body Text
```css
.body-large {
  font-family: var(--font-family-primary);
  font-size: var(--text-lg);
  font-weight: 400;
  line-height: 1.5;
  color: var(--color-gray-700);
}

.body {
  font-family: var(--font-family-primary);
  font-size: var(--text-base);
  font-weight: 400;
  line-height: 1.5;
  color: var(--color-gray-700);
}

.body-small {
  font-family: var(--font-family-primary);
  font-size: var(--text-sm);
  font-weight: 400;
  line-height: 1.4;
  color: var(--color-gray-600);
}
```

#### Labels & Captions
```css
.label {
  font-family: var(--font-family-primary);
  font-size: var(--text-sm);
  font-weight: 500;
  line-height: 1.4;
  color: var(--color-gray-700);
  text-transform: none;
}

.caption {
  font-family: var(--font-family-primary);
  font-size: var(--text-xs);
  font-weight: 400;
  line-height: 1.3;
  color: var(--color-gray-500);
  letter-spacing: 0.025em;
}
```

## Spacing System

### Base Units
```css
:root {
  --space-1: 0.25rem;    /* 4px */
  --space-2: 0.5rem;     /* 8px */
  --space-3: 0.75rem;    /* 12px */
  --space-4: 1rem;       /* 16px */
  --space-5: 1.25rem;    /* 20px */
  --space-6: 1.5rem;     /* 24px */
  --space-8: 2rem;       /* 32px */
  --space-10: 2.5rem;    /* 40px */
  --space-12: 3rem;      /* 48px */
  --space-16: 4rem;      /* 64px */
  --space-20: 5rem;      /* 80px */
  --space-24: 6rem;      /* 96px */
}
```

### Component Spacing
```css
:root {
  /* Widget spacing */
  --widget-padding: var(--space-6);
  --widget-gap: var(--space-4);
  --widget-margin: var(--space-4);

  /* Card spacing */
  --card-padding: var(--space-5);
  --card-gap: var(--space-3);

  /* Button spacing */
  --button-padding-x: var(--space-4);
  --button-padding-y: var(--space-2);
  --button-gap: var(--space-2);

  /* Input spacing */
  --input-padding-x: var(--space-3);
  --input-padding-y: var(--space-2);

  /* Navigation spacing */
  --nav-padding: var(--space-4);
  --nav-item-padding: var(--space-3);
  --nav-gap: var(--space-2);
}
```

## Layout & Grid System

### Container Sizes
```css
:root {
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
  --container-2xl: 1536px;
}

.container {
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  padding-left: var(--space-4);
  padding-right: var(--space-4);
}

@media (min-width: 640px) { .container { max-width: var(--container-sm); } }
@media (min-width: 768px) { .container { max-width: var(--container-md); } }
@media (min-width: 1024px) { .container { max-width: var(--container-lg); } }
@media (min-width: 1280px) { .container { max-width: var(--container-xl); } }
@media (min-width: 1536px) { .container { max-width: var(--container-2xl); } }
```

### Dashboard Grid
```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--space-6);
  padding: var(--space-8);
}

.widget {
  display: flex;
  flex-direction: column;
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: 12px;
  padding: var(--widget-padding);
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

/* Widget size variants */
.widget-1x1 { grid-column: span 1; grid-row: span 1; }
.widget-1x2 { grid-column: span 1; grid-row: span 2; }
.widget-2x1 { grid-column: span 2; grid-row: span 1; }
.widget-2x2 { grid-column: span 2; grid-row: span 2; }
.widget-3x1 { grid-column: span 3; grid-row: span 1; }
.widget-3x2 { grid-column: span 3; grid-row: span 2; }
```

## Components

### Buttons
```css
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--button-gap);
  padding: var(--button-padding-y) var(--button-padding-x);
  font-family: var(--font-family-primary);
  font-size: var(--text-sm);
  font-weight: 500;
  line-height: 1.4;
  text-decoration: none;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.button-primary {
  background: var(--color-primary-500);
  color: white;
  border-color: var(--color-primary-500);
}

.button-primary:hover {
  background: var(--color-primary-600);
  border-color: var(--color-primary-600);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(14, 165, 233, 0.25);
}

.button-secondary {
  background: white;
  color: var(--color-gray-700);
  border-color: var(--color-gray-300);
}

.button-secondary:hover {
  background: var(--color-gray-50);
  border-color: var(--color-gray-400);
}
```

### Forms
```css
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-gray-700);
}

.form-input {
  padding: var(--input-padding-y) var(--input-padding-x);
  font-family: var(--font-family-primary);
  font-size: var(--text-base);
  color: var(--color-gray-900);
  background: white;
  border: 1px solid var(--color-gray-300);
  border-radius: 6px;
  transition: all 0.15s ease;
}

.form-input:focus {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
  border-color: var(--color-primary-500);
}

.form-input[aria-invalid="true"] {
  border-color: var(--color-error-500);
}
```

### Status Indicators
```css
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-xs);
  font-weight: 500;
  border-radius: 9999px;
}

.status-success {
  background: var(--color-success-50);
  color: var(--color-success-700);
  border: 1px solid var(--color-success-200);
}

.status-warning {
  background: var(--color-warning-50);
  color: var(--color-warning-700);
  border: 1px solid var(--color-warning-200);
}

.status-error {
  background: var(--color-error-50);
  color: var(--color-error-700);
  border: 1px solid var(--color-error-200);
}
```

## Icons & Imagery

### Icon System
- **Primary icon library**: Heroicons (outlined and solid variants)
- **Medical icons**: Custom healthcare iconography for dental-specific elements
- **Size variants**: 16px, 20px, 24px, 32px
- **Color**: Inherit parent text color by default

### Icon Usage Guidelines
```css
.icon {
  flex-shrink: 0;
  width: 1.25rem; /* 20px default */
  height: 1.25rem;
}

.icon-sm { width: 1rem; height: 1rem; }      /* 16px */
.icon-md { width: 1.25rem; height: 1.25rem; } /* 20px */
.icon-lg { width: 1.5rem; height: 1.5rem; }   /* 24px */
.icon-xl { width: 2rem; height: 2rem; }       /* 32px */
```

### Medical Imagery
- **X-rays and scans**: High contrast, clinical presentation
- **Patient photos**: Respectful, professional framing
- **Equipment images**: Clean, well-lit, professional photography
- **Staff photos**: Friendly, approachable, professional attire

## Motion & Animation

### Animation Principles
1. **Purposeful**: Every animation serves a functional purpose
2. **Subtle**: Smooth, unobtrusive movements that enhance UX
3. **Fast**: Quick transitions that don't slow down workflows
4. **Accessible**: Respects `prefers-reduced-motion` preferences

### Timing Functions
```css
:root {
  --easing-ease-out: cubic-bezier(0, 0, 0.2, 1);
  --easing-ease-in: cubic-bezier(0.4, 0, 1, 1);
  --easing-ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);

  --duration-fast: 0.15s;
  --duration-base: 0.2s;
  --duration-slow: 0.3s;
  --duration-slower: 0.5s;
}
```

### Common Transitions
```css
.transition-base {
  transition: all var(--duration-base) var(--easing-ease-out);
}

.transition-transform {
  transition: transform var(--duration-base) var(--easing-ease-out);
}

.transition-opacity {
  transition: opacity var(--duration-base) var(--easing-ease-out);
}

.transition-colors {
  transition: background-color var(--duration-base) var(--easing-ease-out),
              border-color var(--duration-base) var(--easing-ease-out),
              color var(--duration-base) var(--easing-ease-out);
}
```

## Accessibility Standards

### WCAG 2.1 AA Compliance Checklist

#### Color & Contrast
- ✅ Text contrast ratio minimum 4.5:1
- ✅ Large text contrast ratio minimum 3:1
- ✅ UI component contrast ratio minimum 3:1
- ✅ Focus indicator contrast ratio minimum 3:1
- ✅ Color not the sole means of conveying information

#### Keyboard Navigation
- ✅ All interactive elements focusable via Tab
- ✅ Focus indicators clearly visible
- ✅ Tab order follows logical reading order
- ✅ Keyboard shortcuts documented and accessible

#### Screen Reader Support
- ✅ Semantic HTML structure
- ✅ ARIA labels for complex UI elements
- ✅ Alt text for all meaningful images
- ✅ Form labels properly associated
- ✅ Live regions for dynamic content

#### Motion & Animation
- ✅ Respects `prefers-reduced-motion`
- ✅ No content flashing more than 3 times per second
- ✅ Animation can be paused or disabled

### Focus Management
```css
:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
  border-radius: 4px;
}

.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--color-primary-500);
  color: white;
  padding: 8px;
  text-decoration: none;
  border-radius: 4px;
  z-index: 1000;
}

.skip-link:focus {
  top: 6px;
}
```

## Responsive Design

### Breakpoints
```css
:root {
  --breakpoint-sm: 640px;   /* Small tablets */
  --breakpoint-md: 768px;   /* Large tablets */
  --breakpoint-lg: 1024px;  /* Small laptops */
  --breakpoint-xl: 1280px;  /* Large laptops */
  --breakpoint-2xl: 1536px; /* Desktop monitors */
}
```

### Mobile-First Approach
```css
/* Mobile styles first (no media query needed) */
.component {
  display: block;
  width: 100%;
}

/* Tablet and up */
@media (min-width: 768px) {
  .component {
    display: flex;
    width: auto;
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .component {
    max-width: 1200px;
  }
}
```

### Touch Targets
- Minimum size: 44px × 44px
- Preferred size: 48px × 48px for primary actions
- Adequate spacing between touch targets (8px minimum)

## Performance Guidelines

### CSS Optimization
- Use CSS custom properties for theming
- Minimize CSS bundle size through tree-shaking
- Leverage browser caching for static assets
- Optimize critical rendering path

### Image Optimization
- WebP format with fallbacks
- Responsive image sets with `srcset`
- Lazy loading for non-critical images
- Appropriate compression levels

### Font Loading
- Font display: swap for better perceived performance
- Preload critical fonts
- Subset fonts to reduce file size
- Use system fonts as fallbacks

## Brand Application

### Logo Usage
- Minimum size: 24px height for digital
- Clear space: Equal to the height of the logo on all sides
- Color variations: Full color, monochrome, reversed
- Placement: Top-left in navigation, center in loading states

### Healthcare Context
- Clean, sterile aesthetic appropriate for medical settings
- Professional color palette that builds trust
- Clear hierarchy that supports quick decision-making
- Consistent with healthcare industry standards

### Multi-System Integration
- Visual distinction for different integrated systems
- Consistent interaction patterns across all platforms
- Unified data presentation standards
- Seamless transitions between system contexts
