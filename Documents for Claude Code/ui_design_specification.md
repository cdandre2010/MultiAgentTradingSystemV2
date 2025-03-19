# Trading Strategy System: UI Design Specification

This document provides detailed UI design specifications for the Trading Strategy System frontend, including user interface components, layouts, interactions, and visual design guidelines.

## Table of Contents
1. [Design Principles](#design-principles)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Layout & Grid System](#layout--grid-system)
5. [Navigation](#navigation)
6. [Core Components](#core-components)
7. [Pages & Screens](#pages--screens)
8. [Conversation Interface](#conversation-interface)
9. [Data Visualization](#data-visualization)
10. [Responsive Design](#responsive-design)
11. [Component Library](#component-library)
12. [Interaction Patterns](#interaction-patterns)
13. [Animation & Transitions](#animation--transitions)

## Design Principles

The UI should follow these core principles:

1. **Clarity**: Financial and trading information must be presented clearly and accurately
2. **Focus**: Minimize distractions during strategy creation and analysis
3. **Guidance**: Provide clear guidance through complex processes
4. **Efficiency**: Optimize for speed and minimize clicks for common tasks
5. **Consistency**: Maintain consistent patterns throughout the application
6. **Accessibility**: Ensure the interface is usable by people with disabilities

## Color Palette

### Primary Colors
- **Primary Blue**: `#2563EB` - Main brand color, used for primary actions and key UI elements
- **Dark Blue**: `#1E40AF` - Used for hover states and secondary elements
- **Light Blue**: `#DBEAFE` - Used for backgrounds and subtle accents

### Secondary Colors
- **Green**: `#10B981` - Used for positive values, success states, and buy indicators
- **Red**: `#EF4444` - Used for negative values, error states, and sell indicators
- **Yellow**: `#F59E0B` - Used for warnings and attention states
- **Purple**: `#8B5CF6` - Used for highlighting AI-related elements

### Neutral Colors
- **White**: `#FFFFFF` - Background for light mode
- **Gray 50**: `#F9FAFB` - Light background for containers
- **Gray 100**: `#F3F4F6` - Background for inputs, cards
- **Gray 200**: `#E5E7EB` - Borders, dividers
- **Gray 400**: `#9CA3AF` - Disabled text, secondary text
- **Gray 600**: `#4B5563` - Body text
- **Gray 800**: `#1F2937` - Headings and important text
- **Gray 900**: `#111827` - Dark text, footer background
- **Black**: `#000000` - Background for dark mode (optional)

### Dark Mode (Optional for MVP)
- **Dark Background**: `#111827` - Main background
- **Dark Surface**: `#1F2937` - Cards, containers
- **Dark Border**: `#374151` - Borders, dividers

## Typography

### Font Family
- **Primary Font**: 'Inter', sans-serif
- **Monospace Font**: 'JetBrains Mono', monospace (for code, data tables)

### Font Sizes
- **Heading 1**: 24px (2rem)
- **Heading 2**: 20px (1.5rem)
- **Heading 3**: 18px (1.25rem)
- **Heading 4**: 16px (1rem)
- **Body**: 14px (0.875rem)
- **Small**: 12px (0.75rem)
- **Tiny**: 11px (0.688rem) - For footnotes, labels

### Font Weights
- **Regular**: 400
- **Medium**: 500
- **Semibold**: 600
- **Bold**: 700

## Layout & Grid System

### Container Widths
- **Max Width**: 1280px
- **Content Width**: 1140px
- **Narrow Content**: 768px (for focused tasks like strategy creation)

### Grid System
- 12-column grid
- Gutter width: 24px (1.5rem)
- Breakpoints:
  - **Small**: 640px
  - **Medium**: 768px
  - **Large**: 1024px
  - **Extra Large**: 1280px

### Spacing Scale
- **4px** (0.25rem): Tiny spacing
- **8px** (0.5rem): Small spacing
- **12px** (0.75rem): Medium spacing
- **16px** (1rem): Default spacing
- **24px** (1.5rem): Large spacing
- **32px** (2rem): Extra large spacing
- **48px** (3rem): Huge spacing

## Navigation

### Main Navigation
- **Dashboard**: Overview of user's strategies and market data
- **Strategies**: List of user's strategies
- **Create**: Start new strategy creation
- **Backtest**: View and manage backtest results
- **Market Data**: Browse available market data
- **Settings**: User profile and preferences

### Secondary Navigation
- **User Menu**: Profile, settings, logout
- **Notifications**: System notifications and alerts
- **Help**: Documentation and support

### Mobile Navigation
- Collapsible hamburger menu
- Bottom navigation bar with key actions

## Core Components

### Buttons

#### Primary Button
- Background: Primary Blue (`#2563EB`)
- Text: White
- Border Radius: 6px
- Padding: 10px 16px
- Hover: Dark Blue (`#1E40AF`)
- Disabled: Gray 400 (`#9CA3AF`)

#### Secondary Button
- Background: White
- Text: Primary Blue (`#2563EB`)
- Border: 1px solid Primary Blue
- Border Radius: 6px
- Padding: 10px 16px
- Hover: Light Blue (`#DBEAFE`) background

#### Tertiary Button
- Background: Transparent
- Text: Gray 600 (`#4B5563`)
- Border: None
- Padding: 10px 16px
- Hover: Gray 100 (`#F3F4F6`) background

### Cards

#### Standard Card
- Background: White
- Border: 1px solid Gray 200 (`#E5E7EB`)
- Border Radius: 8px
- Box Shadow: 0 1px 3px rgba(0, 0, 0, 0.1)
- Padding: 24px

#### Strategy Card
- Same as Standard Card
- Include header with strategy name
- Include strategy type badge
- Show key metrics
- Include action menu

### Forms

#### Input Fields
- Height: 40px
- Border: 1px solid Gray 200 (`#E5E7EB`)
- Border Radius: 6px
- Background: White
- Focus: Border 2px Primary Blue (`#2563EB`)
- Padding: 8px 16px
- Error: Border Red (`#EF4444`)

#### Dropdown
- Same styling as Input Fields
- Include chevron icon
- Show dropdown menu with same border styling

#### Radio & Checkboxes
- Custom styled with brand colors
- Clickable area: 20px × 20px
- Include appropriate animations

#### Slider
- Height: 4px
- Handle: 20px circle
- Track: Gray 200 (`#E5E7EB`)
- Active Track: Primary Blue (`#2563EB`)

### Tables

#### Data Table
- Header:
  - Background: Gray 50 (`#F9FAFB`)
  - Text: Gray 800 (`#1F2937`)
  - Font Weight: Semibold
- Rows:
  - Alternating Background: White / Gray 50 (`#F9FAFB`)
  - Border Bottom: 1px solid Gray 200 (`#E5E7EB`)
  - Hover: Light Blue (`#DBEAFE`)
- Cell Padding: 12px 16px

### Badges & Tags

#### Status Badge
- Border Radius: 12px
- Padding: 4px 8px
- Font Size: 12px
- Font Weight: Medium
- Background Colors:
  - Active: Light Green with Green text
  - Pending: Light Yellow with Yellow text
  - Error: Light Red with Red text

#### Tag
- Border Radius: 4px
- Padding: 4px 8px
- Background: Gray 100 (`#F3F4F6`)
- Text: Gray 600 (`#4B5563`)
- Removable: Include X icon

### Alerts & Notifications

#### Alert
- Border Radius: 6px
- Padding: 16px
- Border Left: 4px solid corresponding color
- Icon on left matching alert type
- Types:
  - Success: Green
  - Warning: Yellow
  - Error: Red
  - Info: Blue

#### Toast Notification
- Position: Top right
- Width: 320px
- Padding: 16px
- Border Radius: 6px
- Box Shadow: 0 4px 6px rgba(0, 0, 0, 0.1)
- Auto-dismiss after 5 seconds
- Include progress bar for timing

## Pages & Screens

### Dashboard

Layout:
- Top navigation bar
- Sidebar with navigation links
- Main content area divided into:
  - Welcome header with user name and quick actions
  - Performance overview cards (4 cards in a row)
  - Strategy summary table (latest strategies)
  - Market overview with key charts
  - Recent activity feed

Components:
- Strategy performance cards
- Quick action buttons
- Market data charts
- Activity timeline

### Strategy Creation

Layout:
- Conversation interface on the right (60% width)
- Strategy builder visualization on the left (40% width)
- Step indicator at the top showing progress

Components:
- Conversation messages
- User input area
- Strategy visualization (updates in real-time)
- Progress stepper
- Action buttons (back, next, save)

### Strategy Detail

Layout:
- Strategy header with name and key metrics
- Tabs for different sections:
  - Overview
  - Components
  - Backtests
  - Settings
- Main content area showing the selected tab

Components:
- Strategy header card
- Tab navigation
- Component visualization
- Performance charts
- Trade history table
- Edit strategy button

### Backtest Results

Layout:
- Backtest header with name and date range
- Key metrics row (4-6 cards)
- Main equity curve chart
- Supporting charts (drawdown, monthly returns)
- Trade list table
- Optimization suggestions

Components:
- Metric cards
- Interactive charts
- Trade table with filtering
- Export buttons
- Optimization action buttons

## Conversation Interface

### Message Types

#### User Message
- Alignment: Right
- Background: Light Blue (`#DBEAFE`)
- Text: Gray 800 (`#1F2937`)
- Border Radius: 12px 12px 0 12px
- Max Width: 70%
- Padding: 12px 16px
- Timestamp: Below message, Gray 400

#### Agent Message
- Alignment: Left
- Background: White
- Border: 1px solid Gray 200 (`#E5E7EB`)
- Text: Gray 800 (`#1F2937`)
- Border Radius: 12px 12px 12px 0
- Max Width: 70%
- Padding: 12px 16px
- Agent Icon: Small circle with agent initial
- Timestamp: Below message, Gray 400

#### System Message
- Alignment: Center
- Background: Gray 50 (`#F9FAFB`)
- Text: Gray 600 (`#4B5563`)
- Border Radius: 12px
- Width: 80%
- Padding: 8px 12px

#### Interactive Elements
- Input options appear inside agent messages
- Selection cards for multiple choice options
- Sliders for numerical inputs
- Date pickers for timeframes

### Conversation Layout

- Message list scrollable, newest at bottom
- Input area fixed at bottom
- "Scroll to bottom" button appears when not at bottom
- Typing indicator shows when agent is responding
- Message groups have visual spacing between topics

## Data Visualization

### Chart Types

#### Line Chart
- Used for: Time-series data, equity curves
- Features:
  - Interactive tooltips
  - Zoom functionality
  - Period comparison
  - Movable legends
  - Customizable timeframes

#### Candlestick Chart
- Used for: Price data
- Features:
  - Volume bars below
  - Technical indicators overlay
  - Timeframe selector
  - Drawing tools (optional for MVP)

#### Bar Chart
- Used for: Performance comparison, monthly returns
- Features:
  - Color coding (positive/negative)
  - Value labels
  - Sorted or chronological

#### Heatmap
- Used for: Correlation matrices, calendar returns
- Features:
  - Color gradient scale
  - Value tooltips
  - Row/column highlighting on hover

#### Gauge Chart
- Used for: Single metrics with context (win rate, Sharpe ratio)
- Features:
  - Color-coded zones
  - Benchmark indicators
  - Current value display

### Chart Styling

- **Colors**: Use consistent color scheme across all charts
- **Grid Lines**: Light gray, subtle
- **Axes**: Clear labels, appropriate scales
- **Tooltips**: Consistent formatting, comprehensive data
- **Legends**: Clear, toggleable series
- **Empty States**: Helpful messages when no data available

## Responsive Design

### Desktop (1024px+)
- Full navigation visible
- Multi-column layouts
- Side-by-side conversation and visualization
- Expanded charts and tables

### Tablet (768px - 1023px)
- Condensed navigation
- Reduced column counts
- Conversation and visualization stacked
- Scrollable tables
- Simplified charts

### Mobile (< 768px)
- Hamburger menu for navigation
- Single column layout
- Full-width components
- Tabs replace side-by-side layouts
- Essential information prioritized
- Simplified charts with limited interactivity

## Component Library

For the MVP, we recommend using **Tailwind CSS** for its:
- Utility-based approach
- Clean, consistent styling
- Strong responsive design support
- Low bundle size
- Customization options

Key Tailwind features to use:
- Custom color scheme with extended theme
- Responsive utilities
- Component classes for consistent styling
- Transition utilities for animations

## Interaction Patterns

### Loading States
- Skeleton screens for content loading
- Spinner for actions and submissions
- Progress bars for long operations (backtests)

### Empty States
- Helpful illustrations
- Clear messaging
- Action buttons to fill content

### Error Handling
- Form validation errors inline with fields
- Toast notifications for system errors
- Fallback UI for component errors

### Success Feedback
- Animated checkmarks for completed actions
- Success messages with next steps
- Automatic progression when appropriate

## Animation & Transitions

### Page Transitions
- Subtle fade transitions between pages (300ms)
- Content slides in from right (new) or left (back)

### Component Animations
- Cards scale slightly on hover (1.02 scale)
- Buttons have hover state transitions (150ms)
- Form elements highlight on focus

### Conversation Animations
- Messages slide and fade in
- Typing indicator pulses
- Smooth scrolling to new messages

### Chart Animations
- Data series animate in on initial load
- Smooth transitions when changing data

## Implementation Guidelines

1. Start with core components and design system
2. Implement layout and navigation structure
3. Build conversation interface as the central feature
4. Add data visualization components
5. Implement responsive design adaptations
6. Add animations and transitions last

This design specification provides a comprehensive guide for building a cohesive, intuitive, and visually appealing frontend for the Trading Strategy System. The focus is on creating a clear, efficient interface that highlights the conversational AI features while providing powerful visualization capabilities for strategy creation and analysis.