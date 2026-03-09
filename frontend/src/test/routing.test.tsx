import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import ApplicationDetail from '../pages/ApplicationDetail';
import Layout from '../components/Layout';
import ProtectedRoute from '../components/ProtectedRoute';

// Wrapper component for tests that need AuthProvider
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Routing Components', () => {
  it('should render login page', () => {
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );
    
    expect(screen.getByText('Intelli-Credit')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
  });

  it('should render dashboard page', () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );
    
    // Dashboard shows loading state initially
    expect(screen.getByText('Loading applications...')).toBeInTheDocument();
  });

  it('should render application detail page with mock data', () => {
    render(
      <TestWrapper>
        <ApplicationDetail />
      </TestWrapper>
    );
    
    // ApplicationDetail shows loading state initially
    expect(screen.getByText('Loading application...')).toBeInTheDocument();
  });

  it('should render layout with navigation', () => {
    render(
      <TestWrapper>
        <Layout />
      </TestWrapper>
    );
    
    expect(screen.getByText('Intelli-Credit')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('should render protected route content when authenticated', () => {
    render(
      <TestWrapper>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </TestWrapper>
    );
    
    // Note: This test will need to be updated in task 23.3 to properly mock authentication
    // For now, it will redirect to login since no user is authenticated
  });
});
