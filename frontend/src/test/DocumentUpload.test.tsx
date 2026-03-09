/**
 * Unit Tests for DocumentUpload Component
 * 
 * Tests file selection, upload progress display, and validation error display.
 * Requirements: 1.1, 1.2, 1.3
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DocumentUpload from '../components/DocumentUpload';
import { documentApi } from '../services/api';

// Mock the API service
vi.mock('../services/api', () => ({
  documentApi: {
    upload: vi.fn(),
  },
}));

describe('DocumentUpload Component', () => {
  const mockApplicationId = 'test-app-123';
  const mockOnUploadComplete = vi.fn();
  const mockOnUploadError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the upload drop zone', () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    expect(screen.getByText('Upload Documents')).toBeInTheDocument();
    expect(screen.getByText(/Drag and drop files here/i)).toBeInTheDocument();
    expect(screen.getByText(/Supported formats: PDF, DOCX, Excel, CSV, Images/i)).toBeInTheDocument();
  });

  it('handles file selection via input', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    // Mock successful upload
    vi.mocked(documentApi.upload).mockResolvedValue({
      id: 'doc-123',
      application_id: mockApplicationId,
      filename: 'test.pdf',
      file_type: 'application/pdf',
      upload_date: new Date().toISOString(),
      processing_status: 'pending',
      storage_url: 'https://example.com/test.pdf',
    });

    // Create a test file
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    // Find the hidden file input
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeInTheDocument();

    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for file to appear in the list
    await waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });

    // Verify upload was called
    await waitFor(() => {
      expect(documentApi.upload).toHaveBeenCalledWith(
        mockApplicationId,
        file,
        'financial_statement'
      );
    });
  });

  it('displays upload progress indicator', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    // Mock upload with delay
    vi.mocked(documentApi.upload).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              id: 'doc-123',
              application_id: mockApplicationId,
              filename: 'test.pdf',
              file_type: 'application/pdf',
              upload_date: new Date().toISOString(),
              processing_status: 'pending',
              storage_url: 'https://example.com/test.pdf',
            });
          }, 100);
        })
    );

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for file to appear
    await waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });

    // Check for loading indicator (spinner icon)
    const loadingIcon = document.querySelector('.animate-spin');
    expect(loadingIcon).toBeInTheDocument();
  });

  it('displays validation error for invalid file type', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    // Create an invalid file type
    const file = new File(['test content'], 'test.exe', { type: 'application/x-msdownload' });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument();
    });

    // Verify upload was NOT called
    expect(documentApi.upload).not.toHaveBeenCalled();
  });

  it('displays validation error for file size exceeding limit', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    // Create a file larger than 10MB
    const largeContent = new Array(11 * 1024 * 1024).fill('a').join('');
    const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });
    
    // Mock the file size
    Object.defineProperty(file, 'size', {
      value: 11 * 1024 * 1024,
      writable: false,
    });

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/File too large/i)).toBeInTheDocument();
    });

    // Verify upload was NOT called
    expect(documentApi.upload).not.toHaveBeenCalled();
  });

  it('handles multiple file selection', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    // Mock successful uploads
    vi.mocked(documentApi.upload).mockResolvedValue({
      id: 'doc-123',
      application_id: mockApplicationId,
      filename: 'test.pdf',
      file_type: 'application/pdf',
      upload_date: new Date().toISOString(),
      processing_status: 'pending',
      storage_url: 'https://example.com/test.pdf',
    });

    // Create multiple test files
    const file1 = new File(['content 1'], 'test1.pdf', { type: 'application/pdf' });
    const file2 = new File(['content 2'], 'test2.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [file1, file2],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for both files to appear
    await waitFor(() => {
      expect(screen.getByText('test1.pdf')).toBeInTheDocument();
      expect(screen.getByText('test2.docx')).toBeInTheDocument();
    });

    // Verify upload was called for both files
    await waitFor(() => {
      expect(documentApi.upload).toHaveBeenCalledTimes(2);
    });
  });

  it('displays success message after successful upload', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    const mockDocId = 'doc-123';
    vi.mocked(documentApi.upload).mockResolvedValue({
      id: mockDocId,
      application_id: mockApplicationId,
      filename: 'test.pdf',
      file_type: 'application/pdf',
      upload_date: new Date().toISOString(),
      processing_status: 'pending',
      storage_url: 'https://example.com/test.pdf',
    });

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText('Upload complete')).toBeInTheDocument();
    });

    // Verify callback was called
    expect(mockOnUploadComplete).toHaveBeenCalledWith(mockDocId);
  });

  it('displays error message when upload fails', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    const errorMessage = 'Network error';
    vi.mocked(documentApi.upload).mockRejectedValue(new Error(errorMessage));

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Verify error callback was called
    expect(mockOnUploadError).toHaveBeenCalledWith(errorMessage);
  });

  it('allows removing files from the list', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    vi.mocked(documentApi.upload).mockResolvedValue({
      id: 'doc-123',
      application_id: mockApplicationId,
      filename: 'test.pdf',
      file_type: 'application/pdf',
      upload_date: new Date().toISOString(),
      processing_status: 'pending',
      storage_url: 'https://example.com/test.pdf',
    });

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for file to appear
    await waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });

    // Find and click the remove button
    const removeButton = screen.getByLabelText('Remove file');
    fireEvent.click(removeButton);

    // Verify file is removed
    await waitFor(() => {
      expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
    });
  });

  it('handles drag and drop', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    vi.mocked(documentApi.upload).mockResolvedValue({
      id: 'doc-123',
      application_id: mockApplicationId,
      filename: 'test.pdf',
      file_type: 'application/pdf',
      upload_date: new Date().toISOString(),
      processing_status: 'pending',
      storage_url: 'https://example.com/test.pdf',
    });

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const dropZone = screen.getByText('Upload Documents').closest('div');

    // Simulate drag enter
    fireEvent.dragEnter(dropZone!, {
      dataTransfer: {
        files: [file],
      },
    });

    // Check for visual feedback
    await waitFor(() => {
      expect(screen.getByText('Drop files here')).toBeInTheDocument();
    });

    // Simulate drop
    fireEvent.drop(dropZone!, {
      dataTransfer: {
        files: [file],
      },
    });

    // Wait for file to appear
    await waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });
  });

  it('displays file size correctly', async () => {
    render(
      <DocumentUpload
        applicationId={mockApplicationId}
        onUploadComplete={mockOnUploadComplete}
        onUploadError={mockOnUploadError}
      />
    );

    vi.mocked(documentApi.upload).mockResolvedValue({
      id: 'doc-123',
      application_id: mockApplicationId,
      filename: 'test.pdf',
      file_type: 'application/pdf',
      upload_date: new Date().toISOString(),
      processing_status: 'pending',
      storage_url: 'https://example.com/test.pdf',
    });

    // Create a file with known size (1MB)
    const content = new Array(1024 * 1024).fill('a').join('');
    const file = new File([content], 'test.pdf', { type: 'application/pdf' });

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Wait for file size to be displayed - look for the specific "1 MB" text
    await waitFor(() => {
      expect(screen.getByText('1 MB')).toBeInTheDocument();
    });
  });
});
