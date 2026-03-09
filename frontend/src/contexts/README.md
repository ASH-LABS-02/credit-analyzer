# Authentication Context

This directory contains the authentication context for the Intelli-Credit platform.

## AuthContext

The `AuthContext` provides Firebase Authentication integration for the application.

### Features

- **Firebase Authentication Integration**: Uses Firebase Auth for secure user authentication
- **Session Management**: Automatically manages user sessions with `onAuthStateChanged`
- **Login/Logout**: Provides login and logout functions
- **Protected Routes**: Enables route protection based on authentication status
- **Loading States**: Prevents rendering until authentication state is determined

### Usage

#### 1. Wrap your app with AuthProvider

```tsx
import { AuthProvider } from './contexts/AuthContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);
```

#### 2. Use the useAuth hook in components

```tsx
import { useAuth } from '../contexts/AuthContext';

function MyComponent() {
  const { currentUser, login, logout, isAuthenticated, loading } = useAuth();

  // Access current user
  console.log(currentUser?.email);

  // Login
  const handleLogin = async () => {
    try {
      await login(email, password);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  // Logout
  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return <div>...</div>;
}
```

#### 3. Protect routes

```tsx
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
```

### API

#### AuthContextType

```typescript
interface AuthContextType {
  currentUser: User | null;        // Current Firebase user or null
  loading: boolean;                 // True while checking auth state
  login: (email: string, password: string) => Promise<UserCredential>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;         // True if user is logged in
}
```

### Session Management

The AuthContext automatically manages user sessions:

- **Persistent Sessions**: Firebase Auth maintains sessions across page refreshes
- **Auto-logout on Expiration**: Sessions expire based on Firebase Auth settings
- **Real-time Updates**: `onAuthStateChanged` listener updates auth state in real-time

### Error Handling

Login errors are handled with Firebase error codes:

- `auth/invalid-email`: Invalid email format
- `auth/user-disabled`: Account has been disabled
- `auth/user-not-found`: No user found with this email
- `auth/wrong-password`: Incorrect password
- `auth/too-many-requests`: Too many failed attempts

### Requirements Validation

This implementation satisfies:

- **Requirement 8.1**: Firebase Authentication credentials required for system access
- **Requirement 8.2**: Session creation with role-based permissions on successful login
- **Requirement 8.4**: Session expiration enforcement and re-authentication requirement

### Security Considerations

- Passwords are never stored in state or localStorage
- Firebase handles all authentication tokens securely
- Sessions are managed server-side by Firebase
- HTTPS is required for production (enforced by Firebase)
