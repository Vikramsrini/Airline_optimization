# Airline Route Optimization - Design Style Guide

## Design Philosophy

### Visual Language
The application embodies **aeronautical precision meets modern data visualization** - creating an interface that feels both technologically advanced and intuitively human. The design draws inspiration from modern aviation cockpits, air traffic control interfaces, and contemporary data dashboards while maintaining accessibility and elegance.

### Color Palette
**Primary Colors:**
- **Sky Blue**: #4A90E2 (navigation, primary actions, links)
- **Cloud White**: #FAFBFC (backgrounds, cards, content areas)
- **Charcoal**: #2C3E50 (primary text, headers, important information)

**Accent Colors:**
- **Amber**: #F39C12 (warnings, alerts, optimization highlights)
- **Emerald**: #27AE60 (success states, optimized routes, positive metrics)
- **Coral**: #E74C3C (errors, critical weather alerts, negative metrics)

**Neutral Tones:**
- **Mist Gray**: #BDC3C7 (borders, dividers, secondary text)
- **Storm Gray**: #34495E (subtle backgrounds, inactive states)

### Typography
**Primary Font**: Inter (sans-serif) - Clean, modern, highly readable
- **Headers**: Inter Bold, 24-48px for main headings
- **Subheaders**: Inter Semibold, 18-24px for section titles
- **Body Text**: Inter Regular, 14-16px for content
- **UI Elements**: Inter Medium, 12-14px for buttons and labels

**Data Font**: JetBrains Mono (monospace) - For code, coordinates, and technical data
- **Coordinates**: 12px for latitude/longitude displays
- **Flight IDs**: 11px for route identifiers
- **Technical Data**: 13px for Spark job details and metrics

## Visual Effects & Animation

### Core Libraries Integration
**Animation Framework**: Anime.js for smooth, professional transitions
- Route path animations with easing curves
- Weather overlay transitions
- UI element state changes
- Loading and processing indicators

**Data Visualization**: ECharts.js for comprehensive analytics
- Route efficiency comparison charts
- Weather impact analysis graphs
- Performance metrics dashboards
- Historical trend visualizations

**Mapping**: Leaflet.js for interactive route visualization
- Animated flight paths with waypoint markers
- Weather overlay integration
- Zoom and pan interactions
- Custom airport and waypoint icons

**Background Effects**: Shader-park for subtle atmospheric effects
- Gentle cloud movement in hero sections
- Subtle gradient animations
- Depth-based parallax effects

### Specific Visual Effects

**Hero Section Background**:
- Animated gradient flow from deep sky blue to cloud white
- Subtle geometric patterns suggesting flight paths
- Parallax scrolling with aircraft silhouette elements
- Shader-based atmospheric depth effects

**Route Visualization**:
- Animated flight paths with smooth curve transitions
- Waypoint markers with hover effects and detailed tooltips
- Weather overlay with real-time precipitation animations
- Interactive zoom and pan with smooth transitions

**Data Dashboard**:
- Real-time chart updates with smooth value transitions
- Spark job progress animations with completion effects
- Weather data integration with color-coded severity indicators
- Interactive filtering with smooth data transitions

**UI Interactions**:
- Button hover effects with subtle lift and glow
- Dropdown animations with staggered item reveals
- Form input focus states with animated borders
- Loading states with aviation-themed spinners

## Layout & Structure

### Grid System
**Desktop Layout** (1200px+):
- **Header**: 80px height with navigation and branding
- **Hero Section**: 400px height with background image and CTA
- **Main Content**: Flexible grid with sidebar (300px) and content area
- **Footer**: 60px height with minimal branding

**Tablet Layout** (768px-1199px):
- **Header**: 70px height with condensed navigation
- **Hero Section**: 300px height with responsive typography
- **Main Content**: Stacked layout with collapsible sidebar
- **Interactive Elements**: Touch-optimized sizing

**Mobile Layout** (320px-767px):
- **Header**: 60px height with hamburger menu
- **Hero Section**: 250px height with simplified content
- **Main Content**: Single column with full-width components
- **Navigation**: Slide-out drawer with clear hierarchy

### Component Spacing
- **Section Padding**: 40px vertical, 20px horizontal
- **Card Spacing**: 24px between cards, 16px internal padding
- **Button Spacing**: 12px vertical, 16px horizontal margins
- **Form Spacing**: 16px between form elements
- **Text Spacing**: 8px line height, 16px paragraph spacing

## Interactive Elements

### Button Styles
**Primary Button** (Optimization Actions):
- Background: Sky Blue (#4A90E2)
- Text: White, Inter Medium 14px
- Hover: Darker blue (#3A7BC8) with subtle shadow
- Active: Inset shadow with slight scale reduction

**Secondary Button** (Secondary Actions):
- Background: Transparent
- Border: 2px solid Mist Gray (#BDC3C7)
- Text: Charcoal (#2C3E50), Inter Medium 14px
- Hover: Light gray background (#F8F9FA)

**Danger Button** (Critical Actions):
- Background: Coral (#E74C3C)
- Text: White, Inter Medium 14px
- Hover: Darker coral (#C0392B)

### Form Elements
**Input Fields**:
- Border: 1px solid Mist Gray (#BDC3C7)
- Focus: 2px solid Sky Blue (#4A90E2) with subtle glow
- Background: Cloud White (#FAFBFC)
- Text: Charcoal (#2C3E50), Inter Regular 14px

**Dropdowns**:
- Custom styled with aviation-themed icons
- Smooth open/close animations with staggered item reveals
- Search functionality with real-time filtering
- Airport codes displayed with country flags

### Data Display
**Cards**:
- Background: Cloud White (#FAFBFC)
- Border: 1px solid Mist Gray (#BDC3C7)
- Shadow: Subtle drop shadow (0 2px 4px rgba(0,0,0,0.1))
- Hover: Elevated shadow with slight scale increase

**Tables**:
- Alternating row colors for improved readability
- Sortable headers with clear visual indicators
- Responsive design with horizontal scroll on mobile
- Sticky headers for long data sets

## Accessibility & Usability

### Color Contrast
- All text maintains 4.5:1 contrast ratio minimum
- Interactive elements have 3:1 contrast ratio minimum
- Color-blind friendly palette with pattern alternatives
- High contrast mode available for accessibility

### Motion & Animation
- Respect prefers-reduced-motion settings
- All animations are optional and can be disabled
- Loading states provide clear progress indication
- Smooth transitions enhance user experience without being distracting

### Responsive Behavior
- Mobile-first design approach
- Touch-friendly interactive elements (44px minimum)
- Readable typography at all screen sizes
- Optimized performance across devices

This design system creates a cohesive, professional, and engaging user experience that reflects the precision and sophistication of modern aviation technology while remaining accessible and intuitive for users of all technical backgrounds.