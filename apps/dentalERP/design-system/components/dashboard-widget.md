# Dashboard Widget Component

## Overview
The Dashboard Widget is a flexible, reusable container component that displays key metrics, charts, and data visualizations within the dashboard layout. It supports drag-and-drop functionality and role-based customization.

## Design Specifications

### Visual Properties
- **Border Radius**: 12px
- **Border**: 1px solid #e5e7eb (semantic.border.primary)
- **Background**: #ffffff (semantic.background.primary)
- **Box Shadow**: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)
- **Hover Shadow**: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)

### Layout
- **Padding**: 24px (component.widget.padding)
- **Margin**: 16px (component.widget.margin)
- **Gap**: 16px (component.widget.gap)
- **Min Height**: 200px
- **Max Height**: 600px (scrollable content)

### States

#### Default State
```css
.widget {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease-in-out;
}
```

#### Hover State
```css
.widget:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}
```

#### Drag State
```css
.widget.dragging {
  opacity: 0.8;
  transform: rotate(2deg);
  z-index: 1000;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}
```

#### Loading State
```css
.widget.loading {
  opacity: 0.6;
  pointer-events: none;
}
.widget.loading::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 24px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #0ea5e9;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
```

### Widget Types

#### Metric Widget
- **Purpose**: Display key performance indicators
- **Components**: Title, value, change indicator, sparkline chart
- **Size**: 1x1 grid unit (minimum)

#### Chart Widget
- **Purpose**: Data visualization (line, bar, pie, area charts)
- **Components**: Title, legend, chart area, data filters
- **Size**: 2x2 grid units (minimum)

#### List Widget
- **Purpose**: Display tabular data or lists
- **Components**: Title, search/filter bar, scrollable content area
- **Size**: 2x1 grid units (minimum)

#### Action Widget
- **Purpose**: Quick actions and shortcuts
- **Components**: Title, action buttons, status indicators
- **Size**: 1x1 grid unit

### Header Structure
```html
<div class="widget-header">
  <div class="widget-title">
    <h3 class="heading-3">Widget Title</h3>
    <span class="widget-subtitle body-small">Subtitle text</span>
  </div>
  <div class="widget-actions">
    <button class="icon-button" aria-label="Refresh">
      <!-- Refresh icon -->
    </button>
    <button class="icon-button" aria-label="More options">
      <!-- Menu icon -->
    </button>
  </div>
</div>
```

### Content Area
```html
<div class="widget-content">
  <!-- Dynamic content based on widget type -->
</div>
```

### Footer (Optional)
```html
<div class="widget-footer">
  <div class="widget-meta">
    <span class="caption">Last updated: 2 minutes ago</span>
  </div>
  <div class="widget-actions-secondary">
    <a href="#" class="text-link">View details</a>
  </div>
</div>
```

## Responsive Behavior

### Desktop (1200px+)
- Grid: 12 columns
- Widget sizes: 1x1, 1x2, 2x1, 2x2, 3x2, 4x2
- Drag handles visible on hover

### Tablet (768px - 1199px)
- Grid: 8 columns
- Widget sizes adapt to maintain readability
- Touch-friendly drag handles

### Mobile (< 768px)
- Grid: 2 columns
- All widgets stack vertically
- Simplified controls

## Accessibility

### ARIA Labels
- `role="region"`
- `aria-label="Dashboard widget: [Widget Title]"`
- `aria-live="polite"` for dynamic content
- `aria-expanded` for collapsible widgets

### Keyboard Navigation
- Tab order: Header actions → Content → Footer actions
- Enter/Space to activate buttons
- Arrow keys for chart navigation
- Escape to close dropdowns/modals

### Focus Management
```css
.widget:focus-within {
  outline: 2px solid #0ea5e9;
  outline-offset: 2px;
}
```

## Integration Points

### Data Sources
- Dentrix: Patient metrics, appointments
- DentalIntel: Analytics and insights
- ADP: Payroll and HR data
- Eaglesoft: Practice management metrics

### Event Handlers
- `onWidgetMove`: Handle drag-and-drop repositioning
- `onWidgetResize`: Handle widget size changes
- `onWidgetRefresh`: Handle data refresh requests
- `onWidgetConfigure`: Handle settings changes

### State Management
```javascript
interface WidgetState {
  id: string;
  type: 'metric' | 'chart' | 'list' | 'action';
  position: { x: number; y: number };
  size: { width: number; height: number };
  config: WidgetConfig;
  data: WidgetData;
  loading: boolean;
  error?: string;
}
```

## Performance Considerations
- Lazy loading for off-screen widgets
- Data caching with 5-minute TTL
- Virtual scrolling for large datasets
- Debounced resize/move operations
- Progressive enhancement for chart rendering
