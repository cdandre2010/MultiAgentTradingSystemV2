# Trading Strategy System: API Specifications

This document defines the API endpoints for the Trading Strategy System, including request/response formats, authentication requirements, and examples.

## Table of Contents
1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [User Management API](#user-management-api)
5. [Strategy API](#strategy-api)
6. [Knowledge Graph API](#knowledge-graph-api)
7. [Backtest API](#backtest-api)
8. [WebSocket API](#websocket-api)

## Base URL

All API endpoints are relative to the base URL:
```
http://localhost:8000/api
```

For production:
```
https://api.tradingstrategy.example.com/api
```

## Authentication

Most endpoints require authentication using JWT tokens.

### JWT Authentication

1. Obtain a token via the login endpoint
2. Include the token in the Authorization header:
   ```
   Authorization: Bearer <token>
   ```
3. Tokens expire after 24 hours and need to be refreshed

### Token Refresh

```
POST /auth/refresh
```

Request:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

## Error Handling

All API errors return an appropriate HTTP status code and a JSON response with error details:

```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "Invalid parameter value",
  "details": {
    "field": "period",
    "error": "Value must be between 5 and 50"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_ERROR` | 401 | Invalid or expired token |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `VALIDATION_ERROR` | 400 | Invalid input parameters |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Internal server error |

## User Management API

### Register User

```
POST /auth/register
```

Request:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securePassword123"
}
```

Response:
```json
{
  "user_id": "user_a1b2c3d4",
  "username": "testuser",
  "email": "test@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Login

```
POST /auth/login
```

Request:
```json
{
  "username": "testuser",
  "password": "securePassword123"
}
```

Response:
```json
{
  "user_id": "user_a1b2c3d4",
  "username": "testuser",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Logout

```
POST /auth/logout
```

Request: (with Authorization header)

Response:
```json
{
  "status": "success",
  "message": "Successfully logged out"
}
```

### Get User Profile

```
GET /users/me
```

Request: (with Authorization header)

Response:
```json
{
  "user_id": "user_a1b2c3d4",
  "username": "testuser",
  "email": "test@example.com",
  "created_at": "2023-06-01T12:00:00Z",
  "last_login": "2023-06-01T14:30:00Z",
  "preferences": {
    "theme": "dark",
    "default_instrument": "BTCUSDT",
    "default_frequency": "1h"
  }
}
```

### Update User Preferences

```
PUT /users/preferences
```

Request:
```json
{
  "theme": "dark",
  "default_instrument": "ETHUSDT",
  "default_frequency": "4h",
  "email_notifications": true
}
```

Response:
```json
{
  "status": "success",
  "preferences": {
    "theme": "dark",
    "default_instrument": "ETHUSDT",
    "default_frequency": "4h",
    "email_notifications": true
  }
}
```

## Strategy API

### Create Strategy

```
POST /strategies
```

Request:
```json
{
  "name": "My BTC Momentum Strategy",
  "strategy_type": "momentum",
  "instrument": "BTCUSDT",
  "frequency": "1h",
  "indicators": [
    {
      "name": "RSI",
      "parameters": {
        "period": 14
      }
    },
    {
      "name": "EMA",
      "parameters": {
        "period": 50
      }
    }
  ],
  "conditions": [
    {
      "type": "entry",
      "logic": "RSI < 30"
    },
    {
      "type": "exit",
      "logic": "RSI > 70"
    }
  ],
  "position_sizing": {
    "method": "percent",
    "value": 2
  },
  "risk_management": {
    "stop_loss": 5,
    "take_profit": 10,
    "max_positions": 1
  }
}
```

Response:
```json
{
  "strategy_id": "strat_a1b2c3d4",
  "name": "My BTC Momentum Strategy",
  "created_at": "2023-06-01T15:30:00Z",
  "status": "active"
}
```

### List Strategies

```
GET /strategies
```

Request: (with Authorization header)

Response:
```json