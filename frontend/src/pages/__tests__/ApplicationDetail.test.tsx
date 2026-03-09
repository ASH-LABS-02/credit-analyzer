/**
 * Unit Tests for ApplicationDetail Component
 * 
 * Tests tab navigation, data display, loading states, and user interactions
 * 
 * Requirements: 13.1, 13.4
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ApplicationDetail from '../ApplicationDetail';
import * as api from '../../services/api';

// Mock the API modules
vi.mock('../../services/api', () => ({
  applicationApi: {
    getById: vi.fn(),
  },
  documentApi: {
    list: vi.fn(),
    delete: vi.fn(),
  },
  analysisApi: {
    getResults: vi.fn(),
  },
  searchApi: {
    search: vi.fn(),
  },
}));

// Mock react-router-dom hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: 'test-app-123' }),
    useNavigate: () => vi.fn(),
  };
});

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

// Mock DocumentUpload component
vi.mock('../../components/DocumentUpload', () => ({
  default: ({ onUploadComplete }: any) => (
    <div data-testid="document-upload">
      <button onClick={() => onUploadComplete()}>Upload</button>
    </div>
  ),
}));

describe('ApplicationDetail Component', () => {
  const mockApplication = {
    id: 'test-app-123',
    company_name: 'Test Company Inc.',
    loan_amount: 500000,
    loan_purpose: 'Business expansion',
    applicant_email: 'test@example.com',
    status: 'analysis_complete',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    credit_score: 78,
    recommendation: 'approve',
  };

  const mockDocuments = [
    {
      id: 'doc-1',
      application_id: 'test-app-123',
      filename: 'financial_statement.pdf',
      file_type: 'pdf',
      upload_date: '2024-01-15T10:00:00Z',
      processing_status: 'complete',
      storage_url: 'https://example.com/doc1.pdf',
    },
    {
      id: 'doc-2',
      application_id: 'test-app-123',
      filename: 'bank_statement.pdf',
      file_type: 'pdf',
      upload_date: '2024-01-15T11:00:00Z',
      processing_status: 'processing',
      storage_url: 'https://example.com/doc2.pdf',
    },
  ];

  const mockAnalysisResults = {
    financial_metrics: {
      current_ratio: 2.5,
      debt_to_equity: 0.8,
      roe: 0.15,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (api.applicationApi.getById as any).mockResolvedValue(mockApplication);
    (api.documentApi.list as any).mockResolvedValue({ documents: mockDocuments, total: 2 });
    (api.analysisApi.getResults as any).mockResolvedValue(mockAnalysisResults);
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <ApplicationDetail />
      </BrowserRouter>
    );
  };

  describe('Loading States', () => {
    it('should display loading spinner while fetching application data', () => {
      (api.applicationApi.getById as any).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderComponent();

      expect(screen.getByText('Loading application...')).toBeInTheDocument();
    });

    it('should display application data after loading', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      expect(screen.getByText(/Application ID:/)).toBeInTheDocument();
      expect(screen.getByText(/\$500,000/)).toBeInTheDocument();
    });

    it('should display error message when application fetch fails', async () => {
      (api.applicationApi.getById as any).mockRejectedValue({
        detail: 'Application not found',
      });

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Error loading application')).toBeInTheDocument();
      });

      expect(screen.getByText('Application not found')).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('should render all tab buttons', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /Overview/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Documents/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Financial Analysis/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Risk Assessment/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /CAM Report/i })).toBeInTheDocument();
    });

    it('should switch to Documents tab when clicked', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(screen.getByText('Document Management')).toBeInTheDocument();
      });
    });

    it('should switch to Financial Analysis tab when clicked', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const financialTab = screen.getByRole('button', { name: /Financial Analysis/i });
      fireEvent.click(financialTab);

      await waitFor(() => {
        expect(screen.getByText('No financial analysis available')).toBeInTheDocument();
      });
    });

    it('should maintain active tab state', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(documentsTab).toHaveClass('bg-black');
      });
    });
  });

  describe('Overview Tab', () => {
    it('should display credit score and recommendation', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('78')).toBeInTheDocument();
      });

      expect(screen.getByText('/100')).toBeInTheDocument();
      expect(screen.getByText('Approve')).toBeInTheDocument();
    });

    it('should display key financial metrics when available', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      // Wait for analysis results to load
      await waitFor(() => {
        expect(screen.getByText('2.50')).toBeInTheDocument();
      });

      expect(screen.getByText('0.80')).toBeInTheDocument();
      expect(screen.getByText('15.0%')).toBeInTheDocument();
    });

    it('should show message when analysis is not complete', async () => {
      const pendingApp = { ...mockApplication, status: 'pending', credit_score: undefined };
      (api.applicationApi.getById as any).mockResolvedValue(pendingApp);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Analysis not yet complete')).toBeInTheDocument();
      });
    });

    it('should display loading state while fetching analysis results', async () => {
      (api.analysisApi.getResults as any).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      expect(screen.getByText('Loading analysis results...')).toBeInTheDocument();
    });
  });

  describe('Documents Tab', () => {
    it('should fetch and display documents when tab is active', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(screen.getByText('financial_statement.pdf')).toBeInTheDocument();
      });

      expect(screen.getByText('bank_statement.pdf')).toBeInTheDocument();
    });

    it('should display document upload component', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(screen.getByTestId('document-upload')).toBeInTheDocument();
      });
    });

    it('should refresh document list after upload', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(screen.getByTestId('document-upload')).toBeInTheDocument();
      });

      // Simulate upload completion
      const uploadButton = screen.getByText('Upload');
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(api.documentApi.list).toHaveBeenCalledTimes(2); // Initial + after upload
      });
    });

    it('should display empty state when no documents exist', async () => {
      (api.documentApi.list as any).mockResolvedValue({ documents: [], total: 0 });

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(screen.getByText('No documents uploaded yet')).toBeInTheDocument();
      });
    });

    it('should handle document deletion', async () => {
      (api.documentApi.delete as any).mockResolvedValue(undefined);
      window.confirm = vi.fn(() => true);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(screen.getByText('financial_statement.pdf')).toBeInTheDocument();
      });

      // Find and click delete button (first one)
      const deleteButtons = screen.getAllByTitle('Delete document');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(api.documentApi.delete).toHaveBeenCalledWith('doc-1');
      });
    });

    it('should perform semantic search', async () => {
      const mockSearchResults = [
        {
          doc_id: 'doc-1',
          chunk: 'The company revenue for 2023 was $5 million',
          relevance_score: 0.95,
        },
      ];
      (api.searchApi.search as any).mockResolvedValue({ results: mockSearchResults });

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/What is the company's revenue/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/What is the company's revenue/);
      const searchButton = screen.getByRole('button', { name: /Search/i });

      fireEvent.change(searchInput, { target: { value: 'revenue 2023' } });
      fireEvent.click(searchButton);

      await waitFor(() => {
        expect(api.searchApi.search).toHaveBeenCalledWith('test-app-123', 'revenue 2023');
      });

      await waitFor(() => {
        expect(screen.getByText(/The company revenue for 2023 was \$5 million/)).toBeInTheDocument();
      });
    });
  });

  describe('Data Display', () => {
    it('should format loan amount with commas', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText(/\$500,000/)).toBeInTheDocument();
      });
    });

    it('should format dates correctly', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText(/Jan 15, 2024/)).toBeInTheDocument();
      });
    });

    it('should format status with proper capitalization', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Analysis Complete')).toBeInTheDocument();
      });
    });

    it('should display correct recommendation color', async () => {
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Approve')).toBeInTheDocument();
      });

      const recommendation = screen.getByText('Approve');
      expect(recommendation).toHaveClass('text-green-600');
    });
  });

  describe('Error Handling', () => {
    it('should handle document fetch errors gracefully', async () => {
      (api.documentApi.list as any).mockRejectedValue({
        detail: 'Failed to fetch documents',
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalled();
      });

      consoleSpy.mockRestore();
    });

    it('should handle search errors gracefully', async () => {
      (api.searchApi.search as any).mockRejectedValue({
        detail: 'Search failed',
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Test Company Inc.')).toBeInTheDocument();
      });

      const documentsTab = screen.getByRole('button', { name: /Documents/i });
      fireEvent.click(documentsTab);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/What is the company's revenue/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/What is the company's revenue/);
      const searchButton = screen.getByRole('button', { name: /Search/i });

      fireEvent.change(searchInput, { target: { value: 'test query' } });
      fireEvent.click(searchButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalled();
      });

      consoleSpy.mockRestore();
    });
  });
});
