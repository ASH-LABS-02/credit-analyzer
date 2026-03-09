/**
 * CAMTab Component
 * Displays Credit Appraisal Memo with real-time generation
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Download, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { camApi } from '../services/api';
import ReactMarkdown from 'react-markdown';

interface CAMTabProps {
  applicationId: string;
  companyName: string;
}

const CAMTab: React.FC<CAMTabProps> = ({ applicationId, companyName }) => {
  const [camContent, setCamContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);

  // Auto-generate CAM on mount if not exists
  useEffect(() => {
    generateCAM();
  }, [applicationId]);

  const generateCAM = async () => {
    try {
      setGenerating(true);
      setError(null);
      
      const response = await camApi.generateSimple(applicationId);
      setCamContent(response.content);
      setGeneratedAt(response.generated_at);
    } catch (err: any) {
      console.error('Error generating CAM:', err);
      setError(err.response?.data?.detail || 'Failed to generate CAM. Please ensure analysis is complete.');
    } finally {
      setGenerating(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'docx') => {
    try {
      setLoading(true);
      
      // Use the simplified CAM export endpoint
      const response = await fetch(
        `http://localhost:8000/api/v1/applications/${applicationId}/cam-simple/export?format=${format}`,
        {
          method: 'GET',
          headers: {
            'Accept': format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          }
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Export failed');
      }
      
      const blob = await response.blob();
      
      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `CAM_${companyName.replace(/\s+/g, '_')}.${format === 'pdf' ? 'pdf' : 'docx'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Error exporting CAM:', err);
      alert(err.message || 'Failed to export CAM. Make sure the required packages are installed on the backend.');
    } finally {
      setLoading(false);
    }
  };

  if (generating) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-black mx-auto mb-4"></div>
          <p className="text-xl font-bold text-gray-700 mb-2">Generating Credit Appraisal Memo...</p>
          <p className="text-gray-600">This may take a moment as we analyze all data</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16 border-2 border-dashed border-red-300 rounded-lg bg-red-50">
        <AlertCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
        <p className="text-xl font-bold text-red-700 mb-2">CAM Generation Failed</p>
        <p className="text-red-600 mb-6 max-w-md mx-auto">{error}</p>
        <button
          onClick={generateCAM}
          className="bg-black text-white px-8 py-3 text-lg font-medium hover:bg-gray-800 transition-colors rounded-lg shadow-lg"
        >
          <RefreshCw className="w-5 h-5 inline mr-2" />
          Retry Generation
        </button>
      </div>
    );
  }

  if (!camContent) {
    return (
      <div className="text-center py-16 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
        <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-xl font-bold text-gray-700 mb-2">No CAM Available</p>
        <p className="text-gray-600 mb-6">Generate a Credit Appraisal Memo to view it here</p>
        <button
          onClick={generateCAM}
          disabled={generating}
          className="bg-black text-white px-8 py-3 text-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 rounded-lg shadow-lg"
        >
          {generating ? 'Generating...' : 'Generate CAM'}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-black mb-2">Credit Appraisal Memo</h2>
          {generatedAt && (
            <p className="text-sm text-gray-600 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              Generated on {new Date(generatedAt).toLocaleString()}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={generateCAM}
            disabled={generating || loading}
            className="flex items-center gap-2 bg-gray-100 text-black px-4 py-2 font-medium hover:bg-gray-200 transition-colors disabled:bg-gray-300 rounded-lg border-2 border-gray-300"
          >
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            Regenerate
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={loading || generating}
            className="flex items-center gap-2 bg-black text-white px-4 py-2 font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 rounded-lg"
          >
            <Download className="w-4 h-4" />
            Export PDF
          </button>
          <button
            onClick={() => handleExport('docx')}
            disabled={loading || generating}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-400 rounded-lg"
          >
            <Download className="w-4 h-4" />
            Export Word
          </button>
        </div>
      </div>

      {/* CAM Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-2 border-gray-300 rounded-lg shadow-lg bg-white"
      >
        <div className="p-8 md:p-12 prose prose-lg max-w-none">
          <ReactMarkdown
            components={{
              h1: ({ node, ...props }) => <h1 className="text-4xl font-bold text-black mb-6 pb-4 border-b-2 border-gray-300" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-2xl font-bold text-black mt-8 mb-4" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-xl font-bold text-black mt-6 mb-3" {...props} />,
              p: ({ node, ...props }) => <p className="text-gray-800 leading-relaxed mb-4" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-2 mb-4 text-gray-800" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-inside space-y-2 mb-4 text-gray-800" {...props} />,
              li: ({ node, ...props }) => <li className="text-gray-800" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-bold text-black" {...props} />,
              em: ({ node, ...props }) => <em className="italic text-gray-700" {...props} />,
              blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-700 my-4" {...props} />,
              hr: ({ node, ...props }) => <hr className="my-8 border-t-2 border-gray-300" {...props} />,
              table: ({ node, ...props }) => <table className="min-w-full border-2 border-gray-300 my-6" {...props} />,
              thead: ({ node, ...props }) => <thead className="bg-gray-100" {...props} />,
              tbody: ({ node, ...props }) => <tbody className="divide-y divide-gray-200" {...props} />,
              tr: ({ node, ...props }) => <tr {...props} />,
              th: ({ node, ...props }) => <th className="px-4 py-3 text-left text-sm font-bold text-black border border-gray-300" {...props} />,
              td: ({ node, ...props }) => <td className="px-4 py-3 text-sm text-gray-800 border border-gray-300" {...props} />,
            }}
          >
            {camContent}
          </ReactMarkdown>
        </div>
      </motion.div>

      {/* Footer */}
      <div className="text-center text-sm text-gray-500 py-4">
        <p>This Credit Appraisal Memo is generated automatically based on analysis results.</p>
        <p>For official use, please review and verify all information before submission.</p>
      </div>
    </div>
  );
};

export default CAMTab;
