/**
 * API Client Service
 * 
 * Axios-based API client with authentication token injection,
 * error handling, and request/response interceptors.
 * 
 * Requirements: 14.2, 14.3
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

// API Base URL - use empty string for same domain in production, localhost for dev
const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined 
  ? import.meta.env.VITE_API_URL 
  : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');

// Application Types
export interface Application {
  id: string;
  company_name: string;
  loan_amount: number;
  loan_purpose: string;
  applicant_email: string;
  status: string;
  created_at: string;
  updated_at: string;
  credit_score?: number;
  recommendation?: string;
}

export interface ApplicationCreate {
  company_name: string;
  loan_amount: number;
  loan_purpose: string;
  applicant_email: string;
}

export interface ApplicationUpdate {
  company_name?: string;
  loan_amount?: number;
  loan_purpose?: string;
  applicant_email?: string;
  status?: string;
  credit_score?: number;
  recommendation?: string;
}

export interface ApplicationListResponse {
  applications: Application[];
  total: number;
  limit?: number;
  status_filter?: string;
}

// Document Types
export interface Document {
  id: string;
  application_id: string;
  filename: string;
  content_type: string;
  document_type?: string;
  uploaded_at: string;
  file_path: string;
  file_size: number;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  application_id: string;
}

// Error Response Type
export interface ApiError {
  detail: string;
  status?: number;
}

/**
 * Create axios instance with base configuration
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Response interceptor - handle errors consistently
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Return successful responses as-is
      return response;
    },
    (error: AxiosError<ApiError>) => {
      // Handle different error scenarios
      if (error.response) {
        // Server responded with error status
        const apiError: ApiError = {
          detail: error.response.data?.detail || 'An error occurred',
          status: error.response.status,
        };

        // Handle specific status codes
        switch (error.response.status) {
          case 401:
            // Unauthorized - token expired or invalid
            console.error('Authentication error:', apiError.detail);
            // Could trigger logout or token refresh here
            break;
          case 403:
            // Forbidden - insufficient permissions
            console.error('Permission denied:', apiError.detail);
            break;
          case 404:
            // Not found
            console.error('Resource not found:', apiError.detail);
            break;
          case 429:
            // Rate limit exceeded
            console.error('Rate limit exceeded:', apiError.detail);
            break;
          case 500:
          case 502:
          case 503:
            // Server errors
            console.error('Server error:', apiError.detail);
            break;
          default:
            console.error('API error:', apiError.detail);
        }

        return Promise.reject(apiError);
      } else if (error.request) {
        // Request made but no response received
        const networkError: ApiError = {
          detail: 'Network error - please check your connection',
          status: 0,
        };
        console.error('Network error:', error.message);
        return Promise.reject(networkError);
      } else {
        // Error setting up the request
        const requestError: ApiError = {
          detail: error.message || 'Request failed',
          status: 0,
        };
        console.error('Request error:', error.message);
        return Promise.reject(requestError);
      }
    }
  );

  return client;
};

// Create singleton instance
const apiClient = createApiClient();

/**
 * Application API Service
 */
export const applicationApi = {
  /**
   * Create a new application
   */
  create: async (data: ApplicationCreate): Promise<Application> => {
    const response = await apiClient.post<Application>('/api/v1/applications', data);
    return response.data;
  },

  /**
   * List all applications with optional filtering
   */
  list: async (params?: { limit?: number; status?: string }): Promise<ApplicationListResponse> => {
    const response = await apiClient.get<ApplicationListResponse>('/api/v1/applications', {
      params,
    });
    return response.data;
  },

  /**
   * Get application by ID
   */
  getById: async (id: string): Promise<Application> => {
    const response = await apiClient.get<Application>(`/api/v1/applications/${id}`);
    return response.data;
  },

  /**
   * Update application
   */
  update: async (id: string, data: ApplicationUpdate): Promise<Application> => {
    const response = await apiClient.patch<Application>(`/api/v1/applications/${id}`, data);
    return response.data;
  },

  /**
   * Delete application
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/applications/${id}`);
  },
};

/**
 * Document API Service
 */
export const documentApi = {
  /**
   * Upload document to application
   */
  upload: async (applicationId: string, file: File, documentType: string = 'financial_statement'): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await apiClient.post<Document>(
      `/api/v1/applications/${applicationId}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * List documents for an application
   */
  list: async (applicationId: string): Promise<DocumentListResponse> => {
    const response = await apiClient.get<DocumentListResponse>(
      `/api/v1/applications/${applicationId}/documents`
    );
    return response.data;
  },

  /**
   * Get document by ID
   */
  getById: async (documentId: string): Promise<Document> => {
    const response = await apiClient.get<Document>(`/api/v1/documents/${documentId}`);
    return response.data;
  },

  /**
   * Download document file
   */
  download: async (documentId: string): Promise<Blob> => {
    const response = await apiClient.get(`/api/v1/documents/${documentId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Delete document
   */
  delete: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/documents/${documentId}`);
  },
};

/**
 * Analysis API Service
 */
export const analysisApi = {
  /**
   * Get analysis results for an application
   */
  getResults: async (applicationId: string): Promise<any> => {
    const response = await apiClient.get(`/api/v1/applications/${applicationId}/results`);
    return response.data;
  },

  /**
   * Trigger analysis for an application
   */
  triggerAnalysis: async (applicationId: string): Promise<any> => {
    const response = await apiClient.post(`/api/v1/applications/${applicationId}/analyze`);
    return response.data;
  },

  /**
   * Trigger simple analysis for an application
   */
  triggerSimpleAnalysis: async (applicationId: string): Promise<any> => {
    const response = await apiClient.post(`/api/v1/applications/${applicationId}/analyze-simple`);
    return response.data;
  },

  /**
   * Get analysis status
   */
  getStatus: async (applicationId: string): Promise<any> => {
    const response = await apiClient.get(`/api/v1/applications/${applicationId}/status`);
    return response.data;
  },
};

/**
 * Search API Service
 */
export const searchApi = {
  /**
   * Perform semantic search across application documents
   */
  search: async (applicationId: string, query: string): Promise<any> => {
    const response = await apiClient.post(`/api/v1/applications/${applicationId}/search`, {
      query,
    });
    return response.data;
  },
};

/**
 * CAM API Service
 */
export const camApi = {
  /**
   * Get CAM content
   */
  getContent: async (applicationId: string): Promise<any> => {
    const response = await apiClient.get(`/api/v1/applications/${applicationId}/cam`);
    return response.data;
  },

  /**
   * Generate CAM
   */
  generate: async (applicationId: string): Promise<any> => {
    const response = await apiClient.post(`/api/v1/applications/${applicationId}/cam`);
    return response.data;
  },

  /**
   * Generate simple CAM (real-time from analysis)
   */
  generateSimple: async (applicationId: string): Promise<any> => {
    const response = await apiClient.post(`/api/v1/applications/${applicationId}/cam-simple`);
    return response.data;
  },

  /**
   * Export CAM
   */
  export: async (applicationId: string, format: 'pdf' | 'docx'): Promise<Blob> => {
    const response = await apiClient.get(`/api/v1/applications/${applicationId}/cam/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },
};

// Export the client for custom requests if needed
export default apiClient;
