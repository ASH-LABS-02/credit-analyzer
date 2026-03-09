import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { FileText, Clock, CheckCircle, XCircle, AlertCircle, Search, Filter, X } from 'lucide-react';
import { applicationApi, Application, ApiError, ApplicationCreate } from '../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [filteredApplications, setFilteredApplications] = useState<Application[]>([]);
  
  // New Application Modal State
  const [showNewAppModal, setShowNewAppModal] = useState(false);
  const [newAppLoading, setNewAppLoading] = useState(false);
  const [newAppError, setNewAppError] = useState<string | null>(null);
  const [newAppData, setNewAppData] = useState<ApplicationCreate>({
    company_name: '',
    loan_amount: 0,
    loan_purpose: '',
    applicant_email: '',
  });

  // Fetch applications from API
  useEffect(() => {
    const fetchApplications = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await applicationApi.list();
        setApplications(response.applications);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to load applications');
        console.error('Error fetching applications:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchApplications();
  }, []);

  // Filter applications based on search and status
  useEffect(() => {
    let filtered = applications;

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(app => app.status === statusFilter);
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(app =>
        app.company_name.toLowerCase().includes(query) ||
        app.loan_purpose.toLowerCase().includes(query) ||
        app.applicant_email.toLowerCase().includes(query)
      );
    }

    setFilteredApplications(filtered);
  }, [applications, searchQuery, statusFilter]);

  const handleCreateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newAppData.company_name || !newAppData.loan_amount || !newAppData.loan_purpose || !newAppData.applicant_email) {
      setNewAppError('Please fill in all fields');
      return;
    }

    setNewAppLoading(true);
    setNewAppError(null);

    try {
      const createdApp = await applicationApi.create(newAppData);
      setApplications([createdApp, ...applications]);
      setShowNewAppModal(false);
      setNewAppData({
        company_name: '',
        loan_amount: 0,
        loan_purpose: '',
        applicant_email: '',
      });
      // Navigate to the new application
      navigate(`/applications/${createdApp.id}`);
    } catch (err) {
      const apiError = err as ApiError;
      setNewAppError(apiError.detail || 'Failed to create application');
    } finally {
      setNewAppLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <FileText className="w-5 h-5" />;
      case 'processing':
        return <Clock className="w-5 h-5" />;
      case 'analysis_complete':
        return <CheckCircle className="w-5 h-5" />;
      case 'approved':
      case 'approved_with_conditions':
        return <CheckCircle className="w-5 h-5" />;
      case 'rejected':
        return <XCircle className="w-5 h-5" />;
      default:
        return <FileText className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-gray-600 bg-gray-100';
      case 'processing':
        return 'text-blue-600 bg-blue-100';
      case 'analysis_complete':
        return 'text-purple-600 bg-purple-100';
      case 'approved':
        return 'text-green-600 bg-green-100';
      case 'approved_with_conditions':
        return 'text-yellow-600 bg-yellow-100';
      case 'rejected':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatStatus = (status: string) => {
    return status
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
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
          <p className="text-gray-600">Loading applications...</p>
        </motion.div>
      </div>
    );
  }

  if (error) {
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
          <p className="text-red-600 font-semibold mb-2">Error loading applications</p>
          <p className="text-gray-600 text-sm mb-6">{error}</p>
          <motion.button
            onClick={() => window.location.reload()}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-black text-white px-6 py-3 rounded-xl font-medium hover:bg-gray-800 transition-all duration-200"
          >
            Retry
          </motion.button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Premium Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex justify-between items-center"
      >
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Applications</h1>
          <p className="text-gray-500">Manage and review credit applications</p>
        </div>
        <motion.button 
          onClick={() => setShowNewAppModal(true)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="bg-black text-white px-8 py-3 rounded-xl font-medium hover:bg-gray-800 transition-all duration-200 shadow-lg"
        >
          New Application
        </motion.button>
      </motion.div>

      {/* Premium Search and Filter Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="flex gap-4 items-center"
      >
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search by company name, purpose, or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:border-black focus:outline-none focus:ring-2 focus:ring-black/5 transition-all duration-200"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-12 pr-10 py-3 border border-gray-300 rounded-xl focus:border-black focus:outline-none focus:ring-2 focus:ring-black/5 appearance-none bg-white cursor-pointer transition-all duration-200 min-w-[200px]"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="analysis_complete">Analysis Complete</option>
            <option value="approved">Approved</option>
            <option value="approved_with_conditions">Approved with Conditions</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </motion.div>

      {/* Results count */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.2 }}
        className="text-sm text-gray-500"
      >
        Showing <span className="font-semibold text-gray-900">{filteredApplications.length}</span> of <span className="font-semibold text-gray-900">{applications.length}</span> applications
      </motion.div>

      {/* Premium Applications List */}
      <div className="grid gap-4">
        {filteredApplications.map((app, index) => (
          <motion.div
            key={app.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            onClick={() => navigate(`/applications/${app.id}`)}
            whileHover={{ scale: 1.01, y: -2 }}
            className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-xl hover:border-gray-300 transition-all duration-200 cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <h3 className="text-xl font-bold text-gray-900">{app.company_name}</h3>
                  <span
                    className={`px-3 py-1.5 text-xs font-semibold flex items-center gap-2 rounded-full ${getStatusColor(
                      app.status
                    )}`}
                  >
                    {getStatusIcon(app.status)}
                    {formatStatus(app.status)}
                  </span>
                </div>
                <div className="flex gap-8 text-sm text-gray-600 mb-3">
                  <span className="flex items-center gap-2">
                    <span className="text-gray-400">Loan Amount:</span>
                    <span className="font-semibold text-gray-900">${app.loan_amount.toLocaleString()}</span>
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="text-gray-400">Created:</span>
                    <span className="font-medium text-gray-900">{formatDate(app.created_at)}</span>
                  </span>
                  {app.credit_score !== undefined && app.credit_score !== null && (
                    <span className="flex items-center gap-2">
                      <span className="text-gray-400">Credit Score:</span>
                      <span className="font-semibold text-gray-900">{app.credit_score}/100</span>
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">
                  <span className="text-gray-400">Purpose:</span> <span className="text-gray-700">{app.loan_purpose}</span>
                </p>
              </div>
              <motion.span
                whileHover={{ x: 5 }}
                className="text-gray-900 hover:text-black font-medium flex items-center gap-2 transition-colors duration-200"
              >
                View Details
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </motion.span>
            </div>
          </motion.div>
        ))}
      </div>

      {filteredApplications.length === 0 && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16 rounded-2xl border-2 border-dashed border-gray-300 bg-gray-50"
        >
          <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-900 font-medium mb-1">
            {searchQuery || statusFilter !== 'all' ? 'No applications match your filters' : 'No applications yet'}
          </p>
          <p className="text-gray-500 text-sm">
            {searchQuery || statusFilter !== 'all'
              ? 'Try adjusting your search or filters'
              : 'Create your first application to get started'}
          </p>
        </motion.div>
      )}

      {/* Premium New Application Modal */}
      {showNewAppModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => {
            setShowNewAppModal(false);
            setNewAppError(null);
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-2xl shadow-2xl border border-gray-200 p-8 max-w-md w-full"
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">New Application</h2>
              <button
                onClick={() => {
                  setShowNewAppModal(false);
                  setNewAppError(null);
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {newAppError && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3"
              >
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800">{newAppError}</p>
              </motion.div>
            )}

            <form onSubmit={handleCreateApplication} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company Name *
                </label>
                <input
                  type="text"
                  required
                  value={newAppData.company_name}
                  onChange={(e) => setNewAppData({ ...newAppData, company_name: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-black focus:outline-none focus:ring-2 focus:ring-black/5 transition-all duration-200"
                  placeholder="Acme Corporation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Loan Amount *
                </label>
                <input
                  type="number"
                  required
                  min="0"
                  step="1000"
                  value={newAppData.loan_amount || ''}
                  onChange={(e) => setNewAppData({ ...newAppData, loan_amount: parseFloat(e.target.value) || 0 })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-black focus:outline-none focus:ring-2 focus:ring-black/5 transition-all duration-200"
                  placeholder="500000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Loan Purpose *
                </label>
                <textarea
                  required
                  value={newAppData.loan_purpose}
                  onChange={(e) => setNewAppData({ ...newAppData, loan_purpose: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-black focus:outline-none focus:ring-2 focus:ring-black/5 transition-all duration-200 resize-none"
                  placeholder="Business expansion"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Applicant Email *
                </label>
                <input
                  type="email"
                  required
                  value={newAppData.applicant_email}
                  onChange={(e) => setNewAppData({ ...newAppData, applicant_email: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-black focus:outline-none focus:ring-2 focus:ring-black/5 transition-all duration-200"
                  placeholder="finance@acme.com"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <motion.button
                  type="button"
                  onClick={() => {
                    setShowNewAppModal(false);
                    setNewAppError(null);
                  }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-gray-50 transition-all duration-200"
                  disabled={newAppLoading}
                >
                  Cancel
                </motion.button>
                <motion.button
                  type="submit"
                  whileHover={{ scale: newAppLoading ? 1 : 1.02 }}
                  whileTap={{ scale: newAppLoading ? 1 : 0.98 }}
                  className="flex-1 px-4 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={newAppLoading}
                >
                  {newAppLoading ? 'Creating...' : 'Create Application'}
                </motion.button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};

export default Dashboard;
