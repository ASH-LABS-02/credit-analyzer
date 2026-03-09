import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import ProtectedRoute from '../components/ProtectedRoute';
import * as firebaseAuth from 'firebase/auth';
import React from 'react';

// Test component to access auth context
const TestComponent = () => {
  const { currentUser, loading, isAuthenticated, login, logout } = useAuth();
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="user">{currentUser ? currentUser.email : 'no-user'}</div>
      <button onClick={() => login('test@example.com', 'password123')}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
};

// Wrapper for tests
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Login Flow', () => {
    it('should successfully login with valid credentials', async () => {
      // Mock successful login
      const mockUser = {
        uid: 'test-uid',
        email: 'test@example.com',
        emailVerified: true,
      };

      const mockUserCredential = {
        user: mockUser,
      };

      vi.mocked(firebaseAuth.signInWithEmailAndPassword).mockResolvedValue(
        mockUserCredential as any
      );

      // Mock onAuthStateChanged to simulate authenticated state
      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser as any);
        return vi.fn();
      });

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });

      // Click login button
      const loginButton = screen.getByText('Login');
      loginButton.click();

      // Verify signInWithEmailAndPassword was called with correct credentials
      await waitFor(() => {
        expect(firebaseAuth.signInWithEmailAndPassword).toHaveBeenCalledWith(
          expect.anything(),
          'test@example.com',
          'password123'
        );
      });
    });

    it('should handle login failure with invalid credentials', async () => {
      // Mock failed login
      const mockError = new Error('Invalid credentials');
      vi.mocked(firebaseAuth.signInWithEmailAndPassword).mockRejectedValue(mockError);

      const TestComponentWithErrorHandling = () => {
        const { login } = useAuth();
        const [error, setError] = React.useState<string | null>(null);
        
        const handleLogin = async () => {
          try {
            await login('test@example.com', 'password123');
          } catch (err) {
            setError((err as Error).message);
          }
        };
        
        return (
          <div>
            <button onClick={handleLogin}>Login</button>
            {error && <div data-testid="error">{error}</div>}
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestComponentWithErrorHandling />
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByTestId('error')).not.toBeInTheDocument();
      });

      // Click login button
      const loginButton = screen.getByText('Login');
      loginButton.click();

      // Verify error is displayed
      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials');
      });

      // Verify signInWithEmailAndPassword was called
      expect(firebaseAuth.signInWithEmailAndPassword).toHaveBeenCalledWith(
        expect.anything(),
        'test@example.com',
        'password123'
      );
    });

    it('should update authentication state after successful login', async () => {
      const mockUser = {
        uid: 'test-uid',
        email: 'test@example.com',
        emailVerified: true,
      };

      // Initially not authenticated
      let authCallback: any;
      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        authCallback = callback;
        callback(null); // Start with no user
        return vi.fn();
      });

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Wait for initial loading
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });

      // Verify not authenticated initially
      expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user')).toHaveTextContent('no-user');

      // Simulate auth state change to authenticated
      if (authCallback) {
        authCallback(mockUser);
      }

      // Verify authenticated state
      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
      });
    });
  });

  describe('Logout Flow', () => {
    it('should successfully logout authenticated user', async () => {
      const mockUser = {
        uid: 'test-uid',
        email: 'test@example.com',
        emailVerified: true,
      };

      // Start with authenticated user
      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser as any);
        return vi.fn();
      });

      vi.mocked(firebaseAuth.signOut).mockResolvedValue(undefined);

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });

      // Verify initially authenticated
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');

      // Click logout button
      const logoutButton = screen.getByText('Logout');
      logoutButton.click();

      // Verify signOut was called
      await waitFor(() => {
        expect(firebaseAuth.signOut).toHaveBeenCalledWith(expect.anything());
      });
    });

    it('should update authentication state after logout', async () => {
      const mockUser = {
        uid: 'test-uid',
        email: 'test@example.com',
        emailVerified: true,
      };

      let authCallback: any;
      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        authCallback = callback;
        callback(mockUser as any); // Start authenticated
        return vi.fn();
      });

      vi.mocked(firebaseAuth.signOut).mockResolvedValue(undefined);

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });

      // Verify authenticated
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');

      // Simulate logout by changing auth state
      if (authCallback) {
        authCallback(null);
      }

      // Verify not authenticated after logout
      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
        expect(screen.getByTestId('user')).toHaveTextContent('no-user');
      });
    });

    it('should handle logout errors gracefully', async () => {
      const mockUser = {
        uid: 'test-uid',
        email: 'test@example.com',
        emailVerified: true,
      };

      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser as any);
        return vi.fn();
      });

      const mockError = new Error('Logout failed');
      vi.mocked(firebaseAuth.signOut).mockRejectedValue(mockError);

      const TestComponentWithErrorHandling = () => {
        const { logout } = useAuth();
        const [error, setError] = React.useState<string | null>(null);
        
        const handleLogout = async () => {
          try {
            await logout();
          } catch (err) {
            setError((err as Error).message);
          }
        };
        
        return (
          <div>
            <button onClick={handleLogout}>Logout</button>
            {error && <div data-testid="error">{error}</div>}
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestComponentWithErrorHandling />
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByTestId('error')).not.toBeInTheDocument();
      });

      // Click logout button
      const logoutButton = screen.getByText('Logout');
      logoutButton.click();

      // Verify error is displayed
      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Logout failed');
      });

      // Verify signOut was called
      expect(firebaseAuth.signOut).toHaveBeenCalledWith(expect.anything());
    });
  });

  describe('Protected Route Access', () => {
    it('should allow access to protected route when authenticated', async () => {
      const mockUser = {
        uid: 'test-uid',
        email: 'test@example.com',
        emailVerified: true,
      };

      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser as any);
        return vi.fn();
      });

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div data-testid="protected-content">Protected Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      });

      // Verify protected content is rendered
      expect(screen.getByTestId('protected-content')).toHaveTextContent('Protected Content');
    });

    it('should redirect to login when accessing protected route without authentication', async () => {
      // Mock not authenticated
      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(null);
        return vi.fn();
      });

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div data-testid="protected-content">Protected Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      });

      // Verify protected content is not rendered (user is redirected)
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should not render children while loading authentication state', () => {
      // Mock loading state
      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        // Don't call callback to simulate loading
        return vi.fn();
      });

      const { container } = render(
        <TestWrapper>
          <div data-testid="test-content">Test Content</div>
        </TestWrapper>
      );

      // Verify children are not rendered while loading
      expect(screen.queryByTestId('test-content')).not.toBeInTheDocument();
    });

    it('should render children after loading completes', async () => {
      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(null);
        return vi.fn();
      });

      render(
        <TestWrapper>
          <div data-testid="test-content">Test Content</div>
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('test-content')).toBeInTheDocument();
      });

      expect(screen.getByTestId('test-content')).toHaveTextContent('Test Content');
    });
  });

  describe('Session Management', () => {
    it('should maintain session across component re-renders', async () => {
      const mockUser = {
        uid: 'test-uid',
        email: 'test@example.com',
        emailVerified: true,
      };

      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser as any);
        return vi.fn();
      });

      const { rerender } = render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });

      // Verify authenticated
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');

      // Re-render component
      rerender(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Verify still authenticated after re-render
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
    });

    it('should cleanup auth listener on unmount', async () => {
      const mockUnsubscribe = vi.fn();
      
      vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(null);
        return mockUnsubscribe;
      });

      const { unmount } = render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });

      // Unmount component
      unmount();

      // Verify unsubscribe was called
      expect(mockUnsubscribe).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('should throw error when useAuth is used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      const TestComponentOutsideProvider = () => {
        useAuth();
        return <div>Test</div>;
      };

      expect(() => {
        render(
          <BrowserRouter>
            <TestComponentOutsideProvider />
          </BrowserRouter>
        );
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleError.mockRestore();
    });
  });
});
