/**
 * MonitoringDashboard Component - Premium Minimal Design
 * Requirements: 10.3, 10.4, 13.1
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, Bell, CheckCircle, Filter } from 'lucide-react';

const MonitoringDashboard = () => {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [filter, setFilter] = useState('all');

  const mockAlerts = [
    {
      id: '1',
      application_id: 'app-123',
      company_name: 'Tech Solutions Inc.',
      severity: 'high',
      message: 'Significant revenue decline detected',
      created_at: new Date().toISOString(),
      acknowledged: false,
    },
    {
      id: '2',
      application_id: 'app-456',
      company_name: 'Manufacturing Corp',
      severity: 'medium',
      message: 'Industry risk level increased',
      created_at: new Date().toISOString(),
      acknowledged: false,
    },
  ];

  useEffect(() => {
    setAlerts(mockAlerts);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-200 bg-red-50';
      case 'high':
        return 'border-orange-200 bg-orange-50';
      case 'medium':
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return 'text-red-600';
      case 'medium':
        return 'text-yellow-600';
      default:
        return 'text-blue-600';
    }
  };

  const filteredAlerts = filter === 'all' ? alerts : alerts.filter(a => a.severity === filter);

  return (
    <div className="space-y-8">
      {/* Premium Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Monitoring Alerts</h1>
          <p className="text-gray-500">Track post-approval monitoring alerts</p>
        </div>
        <div className="flex items-center gap-3">
          <Filter className="w-5 h-5 text-gray-400" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border border-gray-300 px-4 py-3 rounded-xl focus:border-black focus:outline-none focus:ring-2 focus:ring-black/5 transition-all duration-200"
          >
            <option value="all">All Alerts</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </motion.div>

      {/* Premium Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.map((alert, index) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className={`rounded-2xl border p-6 ${getSeverityColor(alert.severity)} hover:shadow-lg transition-all duration-200`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4 flex-1">
                <div className={`w-10 h-10 rounded-xl bg-white flex items-center justify-center ${getSeverityIcon(alert.severity)}`}>
                  <AlertCircle className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="font-bold text-gray-900 mb-1">{alert.company_name}</p>
                  <p className="text-sm text-gray-700 mb-3">{alert.message}</p>
                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span className="font-medium">
                      {new Date(alert.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                    <span className="px-2 py-1 bg-white rounded-full font-semibold capitalize">
                      {alert.severity}
                    </span>
                  </div>
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="bg-black text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-gray-800 transition-all duration-200"
              >
                Acknowledge
              </motion.button>
            </div>
          </motion.div>
        ))}
      </div>

      {filteredAlerts.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16 rounded-2xl border-2 border-dashed border-gray-300 bg-gray-50"
        >
          <div className="w-16 h-16 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <p className="text-gray-900 font-medium mb-1">No alerts to display</p>
          <p className="text-gray-500 text-sm">All systems are running smoothly</p>
        </motion.div>
      )}
    </div>
  );
};

export default MonitoringDashboard;
