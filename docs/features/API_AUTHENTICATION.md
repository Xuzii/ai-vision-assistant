# API Authentication & Security

Session-based authentication with secure password hashing and access control.

---

## Overview

The authentication system provides:
- Secure password hashing (PBKDF2-HMAC-SHA256)
- Session-based authentication
- 24-hour session expiry
- Access logging
- Password change functionality

---

## Authentication Flow

### 1. Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
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

**Sets Cookie:** `session=<session_token>; HttpOnly; SameSite=Lax`

---

### 2. Check Auth Status

```bash
GET /api/auth/status
```

**Authenticated (200):**
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

**Not Authenticated (401):**
```json
{
  "authenticated": false
}
```

---

### 3. Logout

```bash
POST /api/auth/logout
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Clears Cookie:** Removes session cookie

---

## React Integration

### Authentication Context

```javascript
// AuthContext.js
import { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const api = axios.create({
    baseURL: 'http://localhost:8000',
    withCredentials: true
  });

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const { data } = await api.get('/api/auth/status');
      if (data.authenticated) {
        setUser(data.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const { data } = await api.post('/api/auth/login', {
      username,
      password
    });

    if (data.success) {
      setUser(data.user);
      return { success: true };
    }

    return { success: false, error: data.error };
  };

  const logout = async () => {
    await api.post('/api/auth/logout');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

---

### Login Component

```javascript
import { useState, useContext } from 'react';
import { AuthContext } from './AuthContext';
import { useNavigate } from 'react-router-dom';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(username, password);

    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error || 'Login failed');
    }

    setLoading(false);
  };

  return (
    <div className="login-page">
      <form onSubmit={handleSubmit}>
        <h2>AI Vision Assistant</h2>

        {error && <div className="error">{error}</div>}

        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoFocus
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}
```

---

### Protected Route

```javascript
import { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from './AuthContext';

function ProtectedRoute({ children }) {
  const { user, loading } = useContext(AuthContext);

  if (loading) {
    return <div>Loading...</div>;
  }

  return user ? children : <Navigate to="/login" />;
}

// Usage in App.js
<Route path="/dashboard" element={
  <ProtectedRoute>
    <Dashboard />
  </ProtectedRoute>
} />
```

---

## Password Management

### Change Password

```bash
POST /api/change-password
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

**Success (200):**
```json
{
  "success": true
}
```

**Error (200):**
```json
{
  "success": false,
  "error": "Current password incorrect"
}
```

### React Component

```javascript
function ChangePassword() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setMessage('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setMessage('Password must be at least 8 characters');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage('Password changed successfully');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        setMessage(data.error);
      }
    } catch (error) {
      setMessage('Failed to change password');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Change Password</h3>

      {message && <div className="message">{message}</div>}

      <input
        type="password"
        placeholder="Current Password"
        value={currentPassword}
        onChange={(e) => setCurrentPassword(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="New Password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="Confirm New Password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        required
      />

      <button type="submit">Change Password</button>
    </form>
  );
}
```

---

## Security Features

### Password Hashing

- **Algorithm:** PBKDF2-HMAC-SHA256
- **Iterations:** 100,000
- **Salt:** Unique per user (32 bytes)
- **Stored:** `<algorithm>:<iterations>:<salt>:<hash>`

**Example in database:**
```
pbkdf2:sha256:100000:abc123...:def456...
```

### Session Management

- **Storage:** Server-side (Flask sessions)
- **Cookie:** HttpOnly, SameSite=Lax
- **Expiry:** 24 hours
- **Secret Key:** From `FLASK_SECRET_KEY` environment variable

### Access Logging

All access attempts are logged:
- Successful logins
- Failed login attempts
- API endpoint access
- Logout events

---

## CORS Configuration

For React frontend integration, CORS is enabled:

```python
# In dashboard.py
from flask_cors import CORS

CORS(app, supports_credentials=True, origins=[
    "http://localhost:3000",  # React dev server
    "http://localhost:5173"   # Vite dev server
])
```

**For production, update origins:**
```python
CORS(app, supports_credentials=True, origins=[
    "https://yourdomain.com"
])
```

---

## Axios Configuration

### API Client Setup

```javascript
// api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  withCredentials: true,  // IMPORTANT: Enables session cookies
  headers: {
    'Content-Type': 'application/json'
  }
});

// Intercept 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## Environment Variables

### Backend (.env)

```bash
FLASK_SECRET_KEY=your-secret-key-here-change-this
OPENAI_API_KEY=sk-your-openai-key
```

**Generate secure secret key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Frontend (.env)

```bash
REACT_APP_API_URL=http://localhost:8000

# For production:
# REACT_APP_API_URL=https://api.yourdomain.com
```

---

## Troubleshooting

### "Authentication required" errors

**Cause:** Missing or expired session cookie

**Solutions:**
1. Ensure `withCredentials: true` in axios config
2. Check CORS origins match your frontend URL
3. Verify session hasn't expired (24 hours)
4. Clear browser cookies and login again

### CORS errors

**Cause:** Frontend URL not in allowed origins

**Solutions:**
1. Add your frontend URL to CORS origins in `dashboard.py`
2. Ensure `withCredentials: true` in frontend requests
3. Check browser console for exact CORS error
4. Verify Flask-CORS is installed: `pip install flask-cors`

### Session not persisting

**Cause:** Cookie settings or HTTPS issues

**Solutions:**
1. Ensure `SameSite` cookie attribute is correct
2. For production with HTTPS, set `Secure` flag
3. Check `FLASK_SECRET_KEY` is set
4. Verify cookies are not disabled in browser

---

## Production Deployment

### HTTPS Configuration

For production, enable secure cookies:

```python
# In dashboard.py
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## See Also

- [API Reference](../API_REFERENCE.md) - Complete API documentation
- [Quick Reference](../QUICK_REFERENCE.md) - Common commands
