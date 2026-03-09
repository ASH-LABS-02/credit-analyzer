/**
 * DocumentUpload Component - Premium Minimal Design
 * 
 * Elegant drag-and-drop file upload with subtle animations
 * and premium aesthetics.
 * 
 * Requirements: 1.1, 1.2, 1.3, 13.4
 */

import { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, File, X, CheckCircle, AlertCircle, Loader, 
  FileText, FileSpreadsheet, Image as ImageIcon, 
  FileType
} from 'lucide-react';
import { documentApi } from '../services/api';

// Supported file types with minimal styling
const SUPPORTED_FILE_TYPES = {
  'application/pdf': { extensions: ['.pdf'], icon: FileText, color: '#ef4444', label: 'PDF' },
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': { extensions: ['.docx'], icon: FileText, color: '#3b82f6', label: 'DOCX' },
  'application/msword': { extensions: ['.doc'], icon: FileText, color: '#3b82f6', label: 'DOC' },
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': { extensions: ['.xlsx'], icon: FileSpreadsheet, color: '#10b981', label: 'XLSX' },
  'application/vnd.ms-excel': { extensions: ['.xls'], icon: FileSpreadsheet, color: '#10b981', label: 'XLS' },
  'text/csv': { extensions: ['.csv'], icon: FileSpreadsheet, color: '#10b981', label: 'CSV' },
  'image/jpeg': { extensions: ['.jpg', '.jpeg'], icon: ImageIcon, color: '#8b5cf6', label: 'JPG' },
  'image/png': { extensions: ['.png'], icon: ImageIcon, color: '#8b5cf6', label: 'PNG' },
  'image/gif': { extensions: ['.gif'], icon: ImageIcon, color: '#8b5cf6', label: 'GIF' },
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface UploadFile {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

interface DocumentUploadProps {
  applicationId: string;
  onUploadComplete?: (documentId: string) => void;
  onUploadError?: (error: string) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  applicationId,
  onUploadComplete,
  onUploadError,
}) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Calculate stats
  const successCount = files.filter(f => f.status === 'success').length;
  const uploadingCount = files.filter(f => f.status === 'uploading').length;

  /**
   * Get file type info
   */
  const getFileTypeInfo = (file: File) => {
    for (const [mimeType, info] of Object.entries(SUPPORTED_FILE_TYPES)) {
      if (file.type === mimeType || info.extensions.some(ext => file.name.toLowerCase().endsWith(ext))) {
        return info;
      }
    }
    return { icon: FileType, color: '#6b7280', label: 'FILE' };
  };

  /**
   * Validate file
   */
  const validateFile = (file: File): { valid: boolean; error?: string } => {
    const isValidType = Object.keys(SUPPORTED_FILE_TYPES).includes(file.type) ||
      Object.values(SUPPORTED_FILE_TYPES).some(info => 
        info.extensions.some(ext => file.name.toLowerCase().endsWith(ext))
      );
    
    if (!isValidType) {
      return { valid: false, error: 'Unsupported file type' };
    }

    if (file.size > MAX_FILE_SIZE) {
      return { valid: false, error: 'File exceeds 10MB limit' };
    }

    return { valid: true };
  };

  /**
   * Upload file
   */
  const uploadFileToBackend = async (uploadFile: UploadFile): Promise<void> => {
    try {
      setFiles(prev =>
        prev.map(f => (f.id === uploadFile.id ? { ...f, status: 'uploading' as const } : f))
      );

      const progressInterval = setInterval(() => {
        setFiles(prev =>
          prev.map(f => {
            if (f.id === uploadFile.id && f.progress < 90) {
              return { ...f, progress: f.progress + 10 };
            }
            return f;
          })
        );
      }, 200);

      const document = await documentApi.upload(
        applicationId,
        uploadFile.file,
        'financial_statement'
      );

      clearInterval(progressInterval);

      setFiles(prev =>
        prev.map(f =>
          f.id === uploadFile.id
            ? { ...f, status: 'success' as const, progress: 100 }
            : f
        )
      );

      if (onUploadComplete) {
        onUploadComplete(document.id);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      
      setFiles(prev =>
        prev.map(f =>
          f.id === uploadFile.id
            ? { ...f, status: 'error' as const, error: errorMessage }
            : f
        )
      );

      if (onUploadError) {
        onUploadError(errorMessage);
      }
    }
  };

  /**
   * Handle files
   */
  const handleFiles = useCallback((selectedFiles: FileList | null) => {
    if (!selectedFiles || selectedFiles.length === 0) return;

    const newFiles: UploadFile[] = [];

    Array.from(selectedFiles).forEach(file => {
      const validation = validateFile(file);

      const uploadFile: UploadFile = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        progress: 0,
        status: validation.valid ? 'pending' : 'error',
        error: validation.error,
      };

      newFiles.push(uploadFile);

      if (validation.valid) {
        uploadFile.status = 'uploading';
        uploadFileToBackend(uploadFile);
      }
    });

    setFiles(prev => [...prev, ...newFiles]);
  }, [applicationId]);

  /**
   * Drag handlers
   */
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [handleFiles]);

  const removeFile = useCallback((fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  }, []);

  const handleBrowseClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 10) / 10 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Minimal Stats Bar */}
      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex items-center justify-between px-4 py-3 bg-gray-50 rounded-lg border border-gray-200"
        >
          <div className="flex items-center gap-6 text-sm">
            <span className="text-gray-600">
              <span className="font-semibold text-gray-900">{files.length}</span> files
            </span>
            {uploadingCount > 0 && (
              <span className="text-blue-600 flex items-center gap-1.5">
                <Loader className="w-3.5 h-3.5 animate-spin" />
                <span className="font-medium">{uploadingCount} uploading</span>
              </span>
            )}
            {successCount > 0 && (
              <span className="text-green-600 flex items-center gap-1.5">
                <CheckCircle className="w-3.5 h-3.5" />
                <span className="font-medium">{successCount} complete</span>
              </span>
            )}
          </div>
        </motion.div>
      )}

      {/* Premium Drop Zone */}
      <motion.div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        whileHover={{ scale: 1.005 }}
        whileTap={{ scale: 0.995 }}
        className={`
          relative overflow-hidden rounded-2xl border-2 border-dashed
          transition-all duration-300 cursor-pointer
          ${isDragging 
            ? 'border-black bg-gray-50 shadow-xl' 
            : 'border-gray-300 bg-white hover:border-gray-400 hover:shadow-lg'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={Object.values(SUPPORTED_FILE_TYPES).flatMap(info => info.extensions).join(',')}
          onChange={handleFileInputChange}
          className="hidden"
        />

        <div className="px-8 py-16 text-center">
          {/* Icon */}
          <motion.div
            animate={{ 
              y: isDragging ? -5 : 0,
              scale: isDragging ? 1.1 : 1
            }}
            transition={{ duration: 0.2 }}
            className="mb-6"
          >
            <div className="w-16 h-16 mx-auto bg-black rounded-2xl flex items-center justify-center">
              <Upload className="w-8 h-8 text-white" />
            </div>
          </motion.div>

          {/* Text */}
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {isDragging ? 'Drop files here' : 'Upload Documents'}
          </h3>
          <p className="text-sm text-gray-500 mb-6">
            Drag and drop or click to browse
          </p>

          {/* Format Pills */}
          <div className="flex flex-wrap justify-center gap-2">
            {['PDF', 'DOCX', 'XLSX', 'CSV', 'Images'].map((format) => (
              <span
                key={format}
                className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-full"
              >
                {format}
              </span>
            ))}
          </div>

          <p className="text-xs text-gray-400 mt-4">
            Maximum 10MB per file
          </p>
        </div>

        {/* Subtle gradient overlay on hover */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: isDragging ? 0.05 : 0 }}
          className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-500 pointer-events-none"
        />
      </motion.div>

      {/* Minimal File List */}
      <AnimatePresence mode="popLayout">
        {files.map((uploadFile) => {
          const fileTypeInfo = getFileTypeInfo(uploadFile.file);
          const FileIcon = fileTypeInfo.icon;

          return (
            <motion.div
              key={uploadFile.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className={`
                relative overflow-hidden rounded-xl border bg-white
                transition-all duration-200
                ${uploadFile.status === 'success' ? 'border-green-200 bg-green-50/30' : 
                  uploadFile.status === 'error' ? 'border-red-200 bg-red-50/30' : 
                  uploadFile.status === 'uploading' ? 'border-blue-200 bg-blue-50/30' : 
                  'border-gray-200'}
              `}
            >
              {/* Progress bar background */}
              {uploadFile.status === 'uploading' && (
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadFile.progress}%` }}
                  transition={{ duration: 0.3 }}
                  className="absolute inset-y-0 left-0 bg-blue-100/50"
                />
              )}

              <div className="relative px-4 py-4 flex items-center gap-4">
                {/* Icon */}
                <div className="flex-shrink-0">
                  <div 
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${fileTypeInfo.color}15` }}
                  >
                    <FileIcon 
                      className="w-5 h-5" 
                      style={{ color: fileTypeInfo.color }}
                    />
                  </div>
                </div>

                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {uploadFile.file.name}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-gray-500">
                      {formatFileSize(uploadFile.file.size)}
                    </span>
                    <span className="text-xs text-gray-300">•</span>
                    <span 
                      className="text-xs font-medium"
                      style={{ color: fileTypeInfo.color }}
                    >
                      {fileTypeInfo.label}
                    </span>
                    {uploadFile.status === 'uploading' && (
                      <>
                        <span className="text-xs text-gray-300">•</span>
                        <span className="text-xs text-blue-600 font-medium">
                          {uploadFile.progress}%
                        </span>
                      </>
                    )}
                  </div>

                  {/* Error message */}
                  {uploadFile.status === 'error' && uploadFile.error && (
                    <p className="text-xs text-red-600 mt-1">{uploadFile.error}</p>
                  )}
                </div>

                {/* Status Icon */}
                <div className="flex-shrink-0 flex items-center gap-2">
                  {uploadFile.status === 'uploading' && (
                    <Loader className="w-5 h-5 animate-spin text-blue-600" />
                  )}
                  {uploadFile.status === 'success' && (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  )}
                  {uploadFile.status === 'error' && (
                    <AlertCircle className="w-5 h-5 text-red-600" />
                  )}
                  
                  {/* Remove button */}
                  <button
                    onClick={() => removeFile(uploadFile.id)}
                    className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                    aria-label="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

export default DocumentUpload;
