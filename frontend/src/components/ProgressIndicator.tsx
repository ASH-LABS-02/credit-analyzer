/**
 * ProgressIndicator Component
 * Requirements: 11.5, 13.4
 */

import { motion } from 'framer-motion';
import { Loader, CheckCircle } from 'lucide-react';

interface ProgressIndicatorProps {
  stage: string;
  progress: number;
  estimatedTime?: number;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  stage,
  progress,
  estimatedTime,
}) => {
  const stages = [
    'Document Processing',
    'Financial Analysis',
    'Risk Assessment',
    'CAM Generation',
  ];

  const currentStageIndex = stages.indexOf(stage);

  return (
    <div className="border-2 border-gray-200 p-6">
      <h3 className="text-lg font-bold text-black mb-4">Analysis Progress</h3>
      
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-black">{stage}</span>
          <span className="text-sm text-gray-600">{progress}%</span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-blue-600"
          />
        </div>
        {estimatedTime && (
          <p className="text-xs text-gray-600 mt-2">
            Estimated time remaining: {estimatedTime} seconds
          </p>
        )}
      </div>

      {/* Stage List */}
      <div className="space-y-3">
        {stages.map((s, index) => (
          <div key={s} className="flex items-center gap-3">
            {index < currentStageIndex ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : index === currentStageIndex ? (
              <Loader className="w-5 h-5 text-blue-600 animate-spin" />
            ) : (
              <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
            )}
            <span className={`text-sm ${
              index <= currentStageIndex ? 'text-black font-medium' : 'text-gray-500'
            }`}>
              {s}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressIndicator;
