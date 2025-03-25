# Multi-Agent Trading System Frontend

This is the frontend application for the Multi-Agent Trading System. It provides a user interface for interacting with the trading agent system, visualizing data, and managing trading strategies.

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm or yarn
- Backend API running (usually on http://localhost:8000)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The application will open in your browser at [http://localhost:3000](http://localhost:3000).

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects the app from Create React App

## Features

- User authentication (login, register, protected routes)
- Dashboard for strategy overview
- Data visualization components (coming soon)
- Strategy creation and management
- Integration with agent-based backend

## Project Structure

- `/src` - Source code
  - `/api` - API client and services
  - `/components` - Reusable UI components
    - `/auth` - Authentication-related components
    - `/common` - Shared components
  - `/contexts` - React Context providers
  - `/pages` - Page components
  - `/utils` - Utility functions

## Development Guidelines

- Follow component-based architecture
- Use CSS modules for styling
- Use React Context for state management
- Follow RESTful patterns for API integration
- Implement responsive design for all screen sizes