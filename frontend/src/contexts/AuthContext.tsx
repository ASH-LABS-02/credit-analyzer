import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService, { User, LoginRequest, RegisterRequest } from '../services/auth';

interface AuthContextType {
  currentUser: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const user = authService.getCurrentUser();
        if (user && authService.isAuthenticated()) {
          // Verify token is still valid by fetching current user
          try {
            const freshUser = await authService.me();
            setCurrentUser(freshUser);
          } catch (error) {
            // Token invalid, clear auth
            authService.logout();
            setCurrentUser(null);
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    setLoading(true);
    try {
      const loginData: LoginRequest = { email, password };
      const response = await authService.login(loginData);
      setCurrentUser(response.user);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName?: string): Promise<void> => {
    setLoading(true);
    try {
      const registerData: RegisterRequest = { email, password, full_name: fullName };
      const user = await authService.register(registerData);
      // After registration, automatically log in
      await login(email, password);
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    authService.logout();
    setCurrentUser(null);
  };

  const value: AuthContextType = {
    currentUser,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!currentUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
