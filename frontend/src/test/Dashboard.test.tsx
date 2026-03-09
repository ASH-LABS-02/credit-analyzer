/**
 * Dashboard Component Tests
 * 
 * Tests for application list rendering, filtering functionality,
 * and navigation to application details.
 * 
 * Requirements: 13.1
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import * as api from '../services/api';
import * as firebaseAuth from 'firebase/auth';

// Mock the API module
vi.mock('../services/api', () => ({
  applicationApi: {
    list: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Test wrapper with router
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

// Mock application data
const mockApplications = [
  {
    id: '1',
    company_name: 'Tech Solutions Inc.',
    loan_amount: 500000,
    loan_purpose: 'Equipment purchase',
    applicant_email: 'contact@techsolutions.com',
    status: 'processing',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    company_name: 'Manufacturing Corp',
    loan_amount: 1200000,
    loan_purpose: 'Expansion',
    applicant_email: 'info@manufacturing.com',
    status: 'approved',
    created_at: '2024-01-14T10:00:00Z',
    updated_at: '2024-01-14T10:00:00Z',
    credit_score: 78,
    recommendation: 'approve',
  },
  {
    id: '3',
    company_name: 'Retail Ventures Ltd',
    loan_amount: 300000,
    loan_purpose: 'Working capital',
    applicant_email: 'admin@retailventures.com',
    status: 'rejected',
    created_at: '2024-01-13T10:00:00Z',
    updated_at: '2024-01-13T10:00:00Z',
    credit_score: 32,
    recommendation: 'reject',
  },
  {
    id: '4',
    company_name: 'Startup Innovations',
    loan_amount: 750000,
    loan_purpose: 'Product development',
    applicant_email: 'hello@startup.com',
    status: 'pending',
    created_at: '2024-01-16T10:00:00Z',
    updated_at: '2024-01-16T10:00:00Z',
  },
];

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock authenticated user
    vi.mocked(firebaseAuth.onAuthStateChanged).mockImplementation((auth, callback) => {
      callback({
        uid: 'test-uid',
        email: 'test@example.com',
      } as any);
      return vi.fn();
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Application List Rendering', () => {
    it('should render loading state initially', () => {
      // Mock API to never resolve
      vi.mocked(api.applicationApi.list).mockImplementation(
        () => new Promise(() => {})
      );

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      expect(screen.getByText('Loading applications...')).toBeInTheDocument();
    });

    it('should render application list after successful API call', async () => {
      vi.mocked(api.applicationApi.list).mockResolvedValue({
        applications: mockApplications,
        total: mockApplications.length,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Verify all applications are rendered
      expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      expect(screen.getByText('Manufacturing Corp')).toBeInTheDocument();
      expect(screen.getByText('Retail Ventures Ltd')).toBeInTheDocument();
      expect(screen.getByText('Startup Innovations')).toBeInTheDocument();
    });

    it('should display application details correctly', async () => {
      vi.mocked(api.applicationApi.list).mockResolvedValue({
        applications: [mockApplications[0]],
        total: 1,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Verify loan amount is displayed
      expect(screen.getByText('$500,000')).toBeInTheDocument();
      
      // Verify status is displayed (use getAllByText since it appears in dropdown too)
      const processingElements = screen.getAllByText('Processing');
      expect(processingElements.length).toBeGreaterThan(0);
      
      // Verify purpose is displayed
      expect(screen.getByText(/Equipment purchase/)).toBeInTheDocument();
    });

    it('should display credit score when available', async () => {
      vi.mocked(api.applicationApi.list).mockResolvedValue({
        applications: [mockApplications[1]],
        total: 1,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Manufacturing Corp')).toBeInTheDocument();
      });

      // Verify credit score is displayed
      expect(screen.getByText('78/100')).toBeInTheDocument();
    });

    it('should not display credit score when not available', async () => {
      vi.mocked(api.applicationApi.list).mockResolvedValue({
        applications: [mockApplications[0]],
        total: 1,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Verify credit score is not displayed
      expect(screen.queryByText(/\/100/)).not.toBeInTheDocument();
    });

    it('should render error state when API call fails', async () => {
      const errorMessage = 'Failed to load applications';
      vi.mocked(api.applicationApi.list).mockRejectedValue({
        detail: errorMessage,
        status: 500,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Error loading applications')).toBeInTheDocument();
      });

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should render empty state when no applications exist', async () => {
      vi.mocked(api.applicationApi.list).mockResolvedValue({
        applications: [],
        total: 0,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('No applications yet')).toBeInTheDocument();
      });

      expect(screen.getByText('Create your first application to get started')).toBeInTheDocument();
    });
  });

  describe('Filtering Functionality', () => {
    beforeEach(() => {
      vi.mocked(api.applicationApi.list).mockResolvedValue({
        applications: mockApplications,
        total: mockApplications.length,
      });
    });

    it('should filter applications by search query', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Get search input
      const searchInput = screen.getByPlaceholderText(/Search by company name/);
      
      // Search for "Tech"
      fireEvent.change(searchInput, { target: { value: 'Tech' } });

      // Wait for filter to apply
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
        expect(screen.queryByText('Manufacturing Corp')).not.toBeInTheDocument();
        expect(screen.queryByText('Retail Ventures Ltd')).not.toBeInTheDocument();
      });

      // Verify results count
      expect(screen.getByText('Showing 1 of 4 applications')).toBeInTheDocument();
    });

    it('should filter applications by status', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Get status filter dropdown
      const statusFilter = screen.getByRole('combobox');
      
      // Filter by "approved"
      fireEvent.change(statusFilter, { target: { value: 'approved' } });

      // Wait for filter to apply
      await waitFor(() => {
        expect(screen.getByText('Manufacturing Corp')).toBeInTheDocument();
        expect(screen.queryByText('Tech Solutions Inc.')).not.toBeInTheDocument();
        expect(screen.queryByText('Retail Ventures Ltd')).not.toBeInTheDocument();
      });

      // Verify results count
      expect(screen.getByText('Showing 1 of 4 applications')).toBeInTheDocument();
    });

    it('should combine search and status filters', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Apply status filter
      const statusFilter = screen.getByRole('combobox');
      fireEvent.change(statusFilter, { target: { value: 'processing' } });

      // Apply search filter
      const searchInput = screen.getByPlaceholderText(/Search by company name/);
      fireEvent.change(searchInput, { target: { value: 'Tech' } });

      // Wait for filters to apply
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
        expect(screen.queryByText('Manufacturing Corp')).not.toBeInTheDocument();
      });

      // Verify results count
      expect(screen.getByText('Showing 1 of 4 applications')).toBeInTheDocument();
    });

    it('should show empty state when filters match no applications', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Search for non-existent company
      const searchInput = screen.getByPlaceholderText(/Search by company name/);
      fireEvent.change(searchInput, { target: { value: 'NonExistent Company' } });

      // Wait for filter to apply
      await waitFor(() => {
        expect(screen.getByText('No applications match your filters')).toBeInTheDocument();
      });

      expect(screen.getByText('Try adjusting your search or filters')).toBeInTheDocument();
    });

    it('should search by loan purpose', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Search by purpose
      const searchInput = screen.getByPlaceholderText(/Search by company name/);
      fireEvent.change(searchInput, { target: { value: 'Expansion' } });

      // Wait for filter to apply
      await waitFor(() => {
        expect(screen.getByText('Manufacturing Corp')).toBeInTheDocument();
        expect(screen.queryByText('Tech Solutions Inc.')).not.toBeInTheDocument();
      });
    });

    it('should search by email', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Search by email
      const searchInput = screen.getByPlaceholderText(/Search by company name/);
      fireEvent.change(searchInput, { target: { value: 'admin@retailventures.com' } });

      // Wait for filter to apply
      await waitFor(() => {
        expect(screen.getByText('Retail Ventures Ltd')).toBeInTheDocument();
        expect(screen.queryByText('Tech Solutions Inc.')).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation to Application Details', () => {
    beforeEach(() => {
      vi.mocked(api.applicationApi.list).mockResolvedValue({
        applications: mockApplications,
        total: mockApplications.length,
      });
    });

    it('should navigate to application detail when clicking on application card', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Click on first application
      const applicationCard = screen.getByText('Tech Solutions Inc.').closest('div[class*="cursor-pointer"]');
      expect(applicationCard).toBeInTheDocument();
      
      if (applicationCard) {
        fireEvent.click(applicationCard);
      }

      // Verify navigation was called with correct ID
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/applications/1');
      });
    });

    it('should navigate to correct application when clicking different cards', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Manufacturing Corp')).toBeInTheDocument();
      });

      // Click on second application
      const applicationCard = screen.getByText('Manufacturing Corp').closest('div[class*="cursor-pointer"]');
      expect(applicationCard).toBeInTheDocument();
      
      if (applicationCard) {
        fireEvent.click(applicationCard);
      }

      // Verify navigation was called with correct ID
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/applications/2');
      });
    });
  });

  describe('Status Indicators', () => {
    it('should display correct color coding for different statuses', async () => {
      vi.mocked(api.applicationApi.list).mockResolvedValue({
        applications: mockApplications,
        total: mockApplications.length,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for applications to load
      await waitFor(() => {
        expect(screen.getByText('Tech Solutions Inc.')).toBeInTheDocument();
      });

      // Verify status badges are rendered (use getAllByText since they appear in dropdown too)
      expect(screen.getAllByText('Processing').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Approved').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Rejected').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Pending').length).toBeGreaterThan(0);
    });
  });
});
