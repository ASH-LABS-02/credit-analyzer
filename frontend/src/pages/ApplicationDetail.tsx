import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, TrendingUp, AlertCircle, FileCheck, ArrowLeft, Search, Trash2, Eye, Lightbulb } from 'lucide-react';
import DocumentUpload from '../components/DocumentUpload';
import FinancialAnalysisTab from '../components/FinancialAnalysisTab';
import RiskAssessmentTab from '../components/RiskAssessmentTab';
import OverviewTab from '../components/OverviewTab';
import CAMTab from '../components/CAMTab';
import CompanyInsightsTab from '../components/CompanyInsightsTab';
import {
  applicationApi,
  documentApi,
  analysisApi,
  searchApi,
  Application,
  Document,
  ApiError
} from '../services/api';

const ApplicationDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  // State for application data
  const [application, setApplication] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State for documents
  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);

  // State for analysis results
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // State for search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Fetch application data
  useEffect(() => {
    const fetchApplication = async () => {
      if (!id) return;

      try {
        setLoading(true);
        setError(null);
        const data = await applicationApi.getById(id);
        setApplication(data);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to load application');
        console.error('Error fetching application:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchApplication();
  }, [id]);

  // Fetch documents when Documents tab is active
  useEffect(() => {
    const fetchDocuments = async () => {
      if (!id || activeTab !== 'documents') return;

      try {
        setDocumentsLoading(true);
        const response = await documentApi.list(id);
        setDocuments(response.documents);
      } catch (err) {
        console.error('Error fetching documents:', err);
      } finally {
        setDocumentsLoading(false);
      }
    };

    fetchDocuments();
  }, [id, activeTab]);

  // Fetch analysis results when Overview, Financial, or Risk tab is active
  useEffect(() => {
    const fetchAnalysisResults = async () => {
      if (!id || (activeTab !== 'overview' && activeTab !== 'financial' && activeTab !== 'risk') || !application) return;

      // Only fetch if analysis is complete
      if (application.status !== 'analysis_complete' &&
        application.status !== 'approved' &&
        application.status !== 'approved_with_conditions' &&
        application.status !== 'rejected') {
        return;
      }

      try {
        setAnalysisLoading(true);
        const results = await analysisApi.getResults(id);
        setAnalysisResults(results);
      } catch (err) {
        console.error('Error fetching analysis results:', err);
      } finally {
        setAnalysisLoading(false);
      }
    };

    fetchAnalysisResults();
  }, [id, activeTab, application]);

  // Handle document search
  const handleSearch = async () => {
    if (!id || !searchQuery.trim()) return;

    try {
      setSearchLoading(true);
      const results = await searchApi.search(id, searchQuery);
      setSearchResults(results.results || []);
    } catch (err) {
      console.error('Error searching documents:', err);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // Handle document deletion
  const handleDeleteDocument = async (documentId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await documentApi.delete(documentId);
      setDocuments(documents.filter(doc => doc.id !== documentId));
    } catch (err) {
      console.error('Error deleting document:', err);
      alert('Failed to delete document');
    }
  };

  // Handle document view
  const handleViewDocument = async (docId: string) => {
    try {
      setDocumentsLoading(true);
      
      // Download the file as a blob
      const blob = await documentApi.download(docId);
      
      // Create a URL for the blob and open it in a new tab
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      
      // Cleanup after 1 minute
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (err) {
      console.error('Error viewing document:', err);
      alert('Failed to load document');
    } finally {
      setDocumentsLoading(false);
    }
  };

  // Refresh documents list after upload
  const handleUploadComplete = async () => {
    if (!id) return;
    try {
      const response = await documentApi.list(id);
      setDocuments(response.documents);
    } catch (err) {
      console.error('Error refreshing documents:', err);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: FileText },
    { id: 'documents', label: 'Documents', icon: FileCheck },
    { id: 'insights', label: 'Company Insights', icon: Lightbulb },
    { id: 'financial', label: 'Financial Analysis', icon: TrendingUp },
    { id: 'risk', label: 'Risk Assessment', icon: AlertCircle },
    { id: 'cam', label: 'CAM Report', icon: FileText },
  ];

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatStatus = (status: string) => {
    return status
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getRecommendationColor = (recommendation?: string) => {
    switch (recommendation) {
      case 'approve':
        return 'text-green-600';
      case 'approve_with_conditions':
        return 'text-yellow-600';
      case 'reject':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-gray-600">Loading application...</p>
        </motion.div>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <p className="text-red-600 font-semibold mb-2">Error loading application</p>
          <p className="text-gray-600 text-sm mb-6">{error || 'Application not found'}</p>
          <motion.button
            onClick={() => navigate('/dashboard')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-black text-white px-6 py-3 rounded-xl font-medium hover:bg-gray-800 transition-all duration-200"
          >
            Back to Dashboard
          </motion.button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Premium Back button */}
      <motion.button
        onClick={() => navigate('/dashboard')}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        whileHover={{ x: -5 }}
        className="flex items-center gap-2 text-gray-600 hover:text-black font-medium transition-all duration-200"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </motion.button>

      {/* Premium Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg"
      >
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">{application.company_name}</h1>
            <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-500">Application ID:</span>
                <span className="font-medium text-gray-900">{application.id.slice(0, 8)}...</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">Loan Amount:</span>
                <span className="font-semibold text-gray-900">${application.loan_amount.toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">Status:</span>
                <span className="font-medium text-gray-900">{formatStatus(application.status)}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">Created:</span>
                <span className="font-medium text-gray-900">{formatDate(application.created_at)}</span>
              </div>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-black text-white px-6 py-3 rounded-xl font-medium hover:bg-gray-800 transition-all duration-200 shadow-lg"
          >
            Export CAM
          </motion.button>
        </div>
      </motion.div>

      {/* Premium Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-lg"
      >
        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <motion.button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                whileHover={{ y: -2 }}
                className={`flex-1 px-6 py-4 font-medium transition-all duration-200 flex items-center justify-center gap-2 ${
                  activeTab === tab.id
                    ? 'bg-black text-white'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </motion.button>
            );
          })}
        </div>

        {/* Tab Content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="p-8"
        >
        {activeTab === 'overview' && (
          <OverviewTab
            application={application}
            analysisResults={analysisResults}
            analysisLoading={analysisLoading}
            onRunAnalysis={async () => {
              if (!id) return;
              try {
                setAnalysisLoading(true);
                await analysisApi.triggerSimpleAnalysis(id);
                // Refresh application data
                const updatedApp = await applicationApi.getById(id);
                setApplication(updatedApp);
                // Fetch analysis results
                const results = await analysisApi.getResults(id);
                setAnalysisResults(results);
              } catch (err) {
                console.error('Error triggering analysis:', err);
                alert('Failed to trigger analysis. Make sure documents are uploaded.');
              } finally {
                setAnalysisLoading(false);
              }
            }}
          />
        )}

        {activeTab === 'documents' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-black mb-4">Document Management</h2>
              <p className="text-gray-600 mb-6">
                Upload financial documents, bank statements, tax returns, and other supporting materials.
              </p>
            </div>

            {/* Document Upload Component */}
            <DocumentUpload
              applicationId={id || ''}
              onUploadComplete={handleUploadComplete}
              onUploadError={(error) => {
                console.error('Upload error:', error);
                alert(`Upload failed: ${error}`);
              }}
            />

            {/* Semantic Search */}
            <div className="border-t-2 border-gray-200 pt-6">
              <h3 className="text-lg font-bold text-black mb-3">Search Documents</h3>
              <p className="text-sm text-gray-600 mb-4">
                Use natural language to search across all uploaded documents
              </p>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="e.g., What is the company's revenue for 2023?"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="w-full pl-10 pr-4 py-2 border-2 border-gray-300 focus:border-black focus:outline-none"
                  />
                </div>
                <button
                  onClick={handleSearch}
                  disabled={searchLoading || !searchQuery.trim()}
                  className="bg-black text-white px-6 py-2 font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {searchLoading ? 'Searching...' : 'Search'}
                </button>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="mt-4 space-y-3">
                  <p className="text-sm font-medium text-gray-700">
                    Found {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
                  </p>
                  {searchResults.map((result, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="border-2 border-gray-200 p-4"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <p className="text-sm font-medium text-black">
                          Document: {result.doc_id || 'Unknown'}
                        </p>
                        <span className="text-xs text-gray-500">
                          Relevance: {((result.relevance_score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {result.chunk || result.text || 'No content available'}
                      </p>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Document List */}
            <div className="border-t-2 border-gray-200 pt-6">
              <h3 className="text-lg font-bold text-black mb-4">Uploaded Documents</h3>

              {documentsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mx-auto mb-2"></div>
                    <p className="text-gray-600 text-sm">Loading documents...</p>
                  </div>
                </div>
              ) : documents.length > 0 ? (
                <div className="space-y-3">
                  {documents.map((doc, index) => (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="border-2 border-gray-200 p-4 hover:border-black transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <FileText className="w-5 h-5 text-gray-600" />
                          <div className="flex-1">
                            <p className="font-medium text-black">{doc.filename}</p>
                            <div className="flex gap-4 text-xs text-gray-600 mt-1">
                              <span>Type: {doc.document_type || doc.content_type.split('/')[1]?.toUpperCase() || 'UNKNOWN'}</span>
                              <span>Uploaded: {formatDate(doc.uploaded_at)}</span>
                              <span>Size: {(doc.file_size / 1024).toFixed(2)} KB</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleViewDocument(doc.id)}
                            className="p-2 text-gray-600 hover:text-black hover:bg-gray-100 transition-colors"
                            title="View document"
                            disabled={documentsLoading}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 transition-colors"
                            title="Delete document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 border-2 border-dashed border-gray-300">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">No documents uploaded yet</p>
                  <p className="text-gray-500 text-sm mt-1">
                    Upload your first document to get started
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'insights' && (
          <CompanyInsightsTab
            applicationId={id || ''}
            companyName={application.company_name}
          />
        )}

        {activeTab === 'legal' && (
          <LegalCasesTab
            applicationId={id || ''}
            companyName={application.company_name}
          />
        )}

        {activeTab === 'news' && (
          <NewsInsightsTab
            applicationId={id || ''}
            companyName={application.company_name}
          />
        )}

        {activeTab === 'financial' && (
          <FinancialAnalysisTab
            analysisResults={analysisResults}
            loading={analysisLoading}
          />
        )}

        {activeTab === 'risk' && (
          <RiskAssessmentTab
            application={application}
            analysisResults={analysisResults}
            loading={analysisLoading}
          />
        )}

        {activeTab === 'cam' && (
          <CAMTab
            applicationId={id || ''}
            companyName={application.company_name}
          />
        )}
        </motion.div>
      </motion.div>
    </div>
  );
};

export default ApplicationDetail;
