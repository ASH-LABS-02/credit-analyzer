/**
 * FinancialChart Component
 * 
 * Reusable chart component for displaying financial data with Recharts
 * 
 * Requirements: 4.1, 4.2, 13.2, 13.5
 */

import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';

interface FinancialChartProps {
  data: any[];
  title: string;
  type?: 'line' | 'bar';
  dataKeys: { key: string; name: string; color: string }[];
  xAxisKey?: string;
  yAxisLabel?: string;
  tooltipFormatter?: (value: any) => string;
}

const FinancialChart: React.FC<FinancialChartProps> = ({
  data,
  title,
  type = 'line',
  dataKeys,
  xAxisKey = 'year',
  yAxisLabel,
  tooltipFormatter,
}) => {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border-2 border-gray-800 p-4 shadow-2xl rounded-lg">
          <p className="font-bold text-black mb-3 text-base">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-base font-semibold mb-1" style={{ color: entry.color }}>
              {entry.name}: <span className="font-bold">{tooltipFormatter ? tooltipFormatter(entry.value) : entry.value}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="border-2 border-gray-300 p-8 rounded-lg shadow-lg bg-white"
    >
      <h3 className="text-2xl font-bold text-black mb-6">{title}</h3>
      <ResponsiveContainer width="100%" height={450}>
        {type === 'line' ? (
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d1d5db" strokeWidth={1} />
            <XAxis 
              dataKey={xAxisKey} 
              stroke="#1f2937" 
              style={{ fontSize: '14px', fontWeight: 600 }}
              tick={{ fill: '#1f2937' }}
            />
            <YAxis 
              stroke="#1f2937" 
              style={{ fontSize: '14px', fontWeight: 600 }}
              tick={{ fill: '#1f2937' }}
              label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft', style: { fontSize: '14px', fontWeight: 600 } } : undefined} 
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: '14px', fontWeight: 600, paddingTop: '20px' }}
              iconType="line"
            />
            {dataKeys.map((dk) => (
              <Line
                key={dk.key}
                type="monotone"
                dataKey={dk.key}
                name={dk.name}
                stroke={dk.color}
                strokeWidth={4}
                dot={{ fill: dk.color, r: 6, strokeWidth: 2, stroke: '#fff' }}
                activeDot={{ r: 8, strokeWidth: 2 }}
              />
            ))}
          </LineChart>
        ) : (
          <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d1d5db" strokeWidth={1} />
            <XAxis 
              dataKey={xAxisKey} 
              stroke="#1f2937" 
              style={{ fontSize: '14px', fontWeight: 600 }}
              tick={{ fill: '#1f2937' }}
            />
            <YAxis 
              stroke="#1f2937" 
              style={{ fontSize: '14px', fontWeight: 600 }}
              tick={{ fill: '#1f2937' }}
              label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft', style: { fontSize: '14px', fontWeight: 600 } } : undefined} 
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: '14px', fontWeight: 600, paddingTop: '20px' }}
            />
            {dataKeys.map((dk) => (
              <Bar key={dk.key} dataKey={dk.key} name={dk.name} fill={dk.color} radius={[8, 8, 0, 0]} />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </motion.div>
  );
};

export default FinancialChart;
