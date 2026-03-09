/**
 * Authentication Service
 * 
 * Handles JWT-based authentication with the backend API.
 * Manages token storage and user session.
 */

import apiClient from './api';

export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

/**
 * Authentication API Service
 */
export const authService = {
  /**
   * Register a new user
   */
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/api/v1/auth/register', data);
    return response.data;
  },

  /**
   * Login user and store token
   */
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', data);
    const authData = response.data;
    
    // Store token and user data
    localStorage.setItem(TOKEN_KEY, authData.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(authData.user));
    
    // Set token in axios default headers
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${authData.access_token}`;
    
    return authData;
  },

  /**
   * Logout user and clear token
   */
  logout: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    delete apiClient.defaults.headers.common['Authorization'];
  },

  /**
   * Get current user from storage
   */
  getCurrentUser: (): User | null => {
    const userJson = localStorage.getItem(USER_KEY);
    if (!userJson) return null;
    
    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  },

  /**
   * Get stored token
   */
  getToken: (): string | null => {
    return localStorage.getItem(TOKEN_KEY);
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    return !!authService.getToken();
  },

  /**
   * Initialize auth state (call on app startup)
   */
  initialize: (): void => {
    const token = authService.getToken();
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  },

  /**
   * Get current user info from API
   */
  me: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    // Update stored user data
    localStorage.setItem(USER_KEY, JSON.stringify(response.data));
    return response.data;
  },
};

// Initialize auth on module load
authService.initialize();

export default authService;
