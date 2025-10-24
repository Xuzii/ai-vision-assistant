# Life Tracking API Documentation

## Overview

This document provides complete API documentation for integrating your React front-end with the Life Tracking backend server.

**Base URL:** `http://localhost:8000`

**Authentication:** Session-based (cookies)

**CORS:** Enabled for `http://localhost:3000` and `http://localhost:5173` (React dev servers)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Activities](#activities)
3. [Statistics](#statistics)
4. [Calendar](#calendar)
5. [Cameras](#cameras)
6. [User Management](#user-management)
7. [Error Handling](#error-handling)

---

## Authentication

### 1. Login

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate user and create session

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

**Error Response (401):**
```json
{
  "success": false,
  "error": "Invalid username or password"
}
```

**React Example:**
```javascript
const login = async (username, password) => {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Important for session cookies
    body: JSON.stringify({ username, password })
  });
  return await response.json();
};
```

---

### 2. Logout

**Endpoint:** `POST /api/auth/logout`

**Description:** Clear user session

**Success Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**React Example:**
```javascript
const logout = async () => {
  const response = await fetch('http://localhost:8000/api/auth/logout', {
    method: 'POST',
    credentials: 'include'
  });
  return await response.json();
};
```

---

### 3. Check Auth Status

**Endpoint:** `GET /api/auth/status`

**Description:** Check if user is authenticated

**Success Response (200):**
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

**Error Response (401):**
```json
{
  "authenticated": false
}
```

**React Example:**
```javascript
const checkAuth = async () => {
  const response = await fetch('http://localhost:8000/api/auth/status', {
    credentials: 'include'
  });
  return await response.json();
};
```

---

## Activities

### 4. Get Activities

**Endpoint:** `GET /api/activities`

**Description:** Retrieve activity logs with filtering and pagination

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, default: 100) - Number of activities to return
- `offset` (integer, default: 0) - Pagination offset
- `camera` (string, optional) - Filter by camera name
- `from` (ISO datetime, optional) - Start date filter
- `to` (ISO datetime, optional) - End date filter
- `search` (string, optional) - Search in activity, details, or room

**Success Response (200):**
```json
{
  "activities": [
    {
      "id": 123,
      "timestamp": "2025-10-22T14:30:00",
      "camera_name": "Living Room Camera",
      "room": "Living Room",
      "activity": "Person detected",
      "details": "1 person present, sitting on couch",
      "image_path": "frames/frame_20251022_143000.jpg",
      "cost": 0.0025,
      "tokens_used": 150,
      "detection_used": true
    }
  ],
  "total": 500,
  "limit": 100,
  "offset": 0
}
```

**Error Response (401):**
```json
{
  "success": false,
  "error": "Authentication required",
  "error_type": "auth_required"
}
```

**React Example:**
```javascript
const getActivities = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(`http://localhost:8000/api/activities?${params}`, {
    credentials: 'include'
  });
  return await response.json();
};

// Usage
const activities = await getActivities({
  limit: 50,
  camera: 'Living Room Camera',
  from: '2025-10-22T00:00:00'
});
```

---

## Statistics

### 5. Get Statistics

**Endpoint:** `GET /api/statistics`

**Description:** Get activity statistics and analytics

**Authentication:** Required

**Query Parameters:**
- `period` (string, default: 'today') - Options: `today`, `week`, `month`, `all`

**Success Response (200):**
```json
{
  "period": "today",
  "total_activities": 45,
  "total_cost": 0.1125,
  "by_room": [
    { "room": "Living Room", "count": 20 },
    { "room": "Kitchen", "count": 15 }
  ],
  "by_activity": [
    { "activity": "Person detected", "count": 30 },
    { "activity": "Movement detected", "count": 15 }
  ],
  "by_camera": [
    { "camera_name": "Living Room Camera", "count": 25 },
    { "camera_name": "Kitchen Camera", "count": 20 }
  ],
  "timeline": [
    { "hour": "00:00", "count": 2 },
    { "hour": "01:00", "count": 1 }
  ]
}
```

**React Example:**
```javascript
const getStats = async (period = 'today') => {
  const response = await fetch(`http://localhost:8000/api/statistics?period=${period}`, {
    credentials: 'include'
  });
  return await response.json();
};
```

---

## Calendar

### 6. Get Calendar Events

**Endpoint:** `GET /api/calendar`

**Description:** Get activities formatted for calendar display (FullCalendar compatible)

**Authentication:** Required

**Query Parameters:**
- `from` (ISO datetime, optional) - Start date
- `to` (ISO datetime, optional) - End date

**Success Response (200):**
```json
[
  {
    "id": 123,
    "title": "Living Room - Person detected",
    "start": "2025-10-22T14:30:00",
    "extendedProps": {
      "camera": "Living Room Camera",
      "room": "Living Room",
      "activity": "Person detected",
      "details": "1 person present",
      "image_path": "frames/frame_20251022_143000.jpg",
      "cost": 0.0025
    }
  }
]
```

**React Example:**
```javascript
const getCalendarEvents = async (from, to) => {
  const params = new URLSearchParams({ from, to });
  const response = await fetch(`http://localhost:8000/api/calendar?${params}`, {
    credentials: 'include'
  });
  return await response.json();
};
```

---

## Cameras

### 7. Get Camera List

**Endpoint:** `GET /api/cameras`

**Description:** Get list of configured cameras

**Authentication:** Required

**Success Response (200):**
```json
{
  "cameras": [
    {
      "name": "Living Room Camera",
      "active_hours": {
        "start": "00:00",
        "end": "23:59"
      },
      "capture_interval": 15
    }
  ]
}
```

**React Example:**
```javascript
const getCameras = async () => {
  const response = await fetch('http://localhost:8000/api/cameras', {
    credentials: 'include'
  });
  return await response.json();
};
```

---

### 8. Get Camera Snapshot

**Endpoint:** `GET /api/camera/snapshot/<camera_name>`

**Description:** Get latest captured snapshot from camera

**Authentication:** Required

**Success Response (200):**
```json
{
  "success": true,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Error Response (200):**
```json
{
  "success": false,
  "error": "No snapshot available"
}
```

**React Example:**
```javascript
const getSnapshot = async (cameraName) => {
  const response = await fetch(`http://localhost:8000/api/camera/snapshot/${cameraName}`, {
    credentials: 'include'
  });
  return await response.json();
};

// Display in React
<img src={snapshot.image} alt="Camera snapshot" />
```

---

### 9. Get Live Camera Frame

**Endpoint:** `GET /api/camera/live/<camera_name>`

**Description:** Capture and return a live frame from camera (real-time)

**Authentication:** Required

**Success Response (200):**
```json
{
  "success": true,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Error Responses:**

**Connection Failed (200):**
```json
{
  "success": false,
  "error": "Cannot connect to camera at rtsp://...",
  "error_type": "connection_failed",
  "details": "Camera may be offline...",
  "rtsp_url": "rtsp://..."
}
```

**React Example:**
```javascript
const getLiveFrame = async (cameraName) => {
  const response = await fetch(`http://localhost:8000/api/camera/live/${cameraName}`, {
    credentials: 'include'
  });
  return await response.json();
};
```

---

### 10. Camera Video Stream

**Endpoint:** `GET /api/camera/stream/<camera_name>`

**Description:** MJPEG video stream for continuous live viewing

**Authentication:** Required

**Response:** `multipart/x-mixed-replace` stream

**React Example:**
```javascript
// Simple image tag approach
<img
  src={`http://localhost:8000/api/camera/stream/${cameraName}`}
  alt="Live camera stream"
/>

// Or with credentials handling
const streamUrl = `http://localhost:8000/api/camera/stream/${cameraName}`;
```

---

### 11. Get Frame Image

**Endpoint:** `GET /frames/<filename>`

**Description:** Serve saved frame images

**Authentication:** Required

**Response:** JPEG image file

**React Example:**
```javascript
// Use directly in img src
<img src={`http://localhost:8000/frames/${imagePath}`} alt="Activity frame" />
```

---

## User Management

### 12. Change Password

**Endpoint:** `POST /api/change-password`

**Description:** Change current user's password

**Authentication:** Required

**Request Body:**
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

**Success Response (200):**
```json
{
  "success": true
}
```

**Error Response (200):**
```json
{
  "success": false,
  "error": "Current password incorrect"
}
```

**React Example:**
```javascript
const changePassword = async (currentPassword, newPassword) => {
  const response = await fetch('http://localhost:8000/api/change-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword
    })
  });
  return await response.json();
};
```

---

## Error Handling

All API endpoints follow consistent error handling patterns:

### HTTP Status Codes

- `200` - Success (even for some errors, check `success` field in JSON)
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (authentication required or invalid credentials)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_type": "error_category"
}
```

### Common Error Types

- `auth_required` - User must be authenticated
- `connection_failed` - Camera connection failed
- `capture_failed` - Frame capture failed
- `config_error` - Configuration file issue
- `opencv_error` - OpenCV processing error
- `unknown_error` - Unexpected error

---

## React Integration Guide

### Setting Up Axios (Recommended)

```bash
npm install axios
```

```javascript
// src/api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json'
  }
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Authentication Context Example

```javascript
// src/contexts/AuthContext.jsx
import React, { createContext, useState, useEffect } from 'react';
import apiClient from '../api/client';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await apiClient.get('/api/auth/status');
      if (response.data.authenticated) {
        setUser(response.data.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const response = await apiClient.post('/api/auth/login', {
      username,
      password
    });
    if (response.data.success) {
      setUser(response.data.user);
    }
    return response.data;
  };

  const logout = async () => {
    await apiClient.post('/api/auth/logout');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### Protected Route Component

```javascript
// src/components/ProtectedRoute.jsx
import { Navigate } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);

  if (loading) {
    return <div>Loading...</div>;
  }

  return user ? children : <Navigate to="/login" />;
};
```

### API Service Example

```javascript
// src/services/activityService.js
import apiClient from '../api/client';

export const activityService = {
  getActivities: async (filters = {}) => {
    const response = await apiClient.get('/api/activities', { params: filters });
    return response.data;
  },

  getStatistics: async (period = 'today') => {
    const response = await apiClient.get('/api/statistics', { params: { period } });
    return response.data;
  },

  getCalendarEvents: async (from, to) => {
    const response = await apiClient.get('/api/calendar', { params: { from, to } });
    return response.data;
  }
};

export const cameraService = {
  getCameras: async () => {
    const response = await apiClient.get('/api/cameras');
    return response.data;
  },

  getSnapshot: async (cameraName) => {
    const response = await apiClient.get(`/api/camera/snapshot/${cameraName}`);
    return response.data;
  },

  getLiveFrame: async (cameraName) => {
    const response = await apiClient.get(`/api/camera/live/${cameraName}`);
    return response.data;
  }
};
```

---

## Production Considerations

### CORS Configuration

For production, update the CORS origins in `src/web/dashboard.py`:

```python
CORS(app, supports_credentials=True, origins=["https://yourdomain.com"])
```

### Environment Variables

Update your React `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
# or for production:
# VITE_API_BASE_URL=https://api.yourdomain.com
```

### Session Security

The backend uses secure session-based authentication with:
- Secret key from environment variable `FLASK_SECRET_KEY`
- 24-hour session lifetime
- Secure access logging

---

## Support

For issues or questions, refer to the project README or check the backend logs for detailed error messages.
