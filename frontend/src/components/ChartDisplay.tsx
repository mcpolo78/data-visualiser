"use client";

import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ChartSuggestion {
  type: string;
  title: string;
  x_axis?: string;
  y_axis?: string;
  explanation: string;
  data: any[];
}

interface ChartDisplayProps {
  suggestion: ChartSuggestion;
  index: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const ChartDisplay: React.FC<ChartDisplayProps> = ({ suggestion, index }) => {
  const renderChart = () => {
    const commonProps = {
      width: '100%',
      height: 300,
      data: suggestion.data,
    };

    switch (suggestion.type.toLowerCase()) {
      case 'bar':
        return (
          <ResponsiveContainer {...commonProps}>
            <BarChart data={suggestion.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={suggestion.x_axis} 
                tick={{ fontSize: 12 }}
                interval={0}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar 
                dataKey={suggestion.y_axis} 
                fill={COLORS[index % COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer {...commonProps}>
            <LineChart data={suggestion.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={suggestion.x_axis} 
                tick={{ fontSize: 12 }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey={suggestion.y_axis} 
                stroke={COLORS[index % COLORS.length]}
                strokeWidth={3}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer {...commonProps}>
            <PieChart>
              <Pie
                data={suggestion.data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {suggestion.data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer {...commonProps}>
            <ScatterChart data={suggestion.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={suggestion.x_axis} 
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                dataKey={suggestion.y_axis} 
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Legend />
              <Scatter 
                dataKey={suggestion.y_axis} 
                fill={COLORS[index % COLORS.length]}
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer {...commonProps}>
            <AreaChart data={suggestion.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={suggestion.x_axis} 
                tick={{ fontSize: 12 }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey={suggestion.y_axis} 
                stroke={COLORS[index % COLORS.length]}
                fill={COLORS[index % COLORS.length]}
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
            <p className="text-gray-500">Chart type '{suggestion.type}' not supported</p>
          </div>
        );
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h3 className="text-xl font-semibold text-gray-800 mb-2">
          {suggestion.title}
        </h3>
        <div className="flex items-center space-x-2 mb-3">
          <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
            {suggestion.type.charAt(0).toUpperCase() + suggestion.type.slice(1)} Chart
          </span>
          {suggestion.x_axis && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
              X: {suggestion.x_axis}
            </span>
          )}
          {suggestion.y_axis && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
              Y: {suggestion.y_axis}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 mb-4">
          {suggestion.explanation}
        </p>
      </div>
      
      <div className="h-80">
        {renderChart()}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Showing {suggestion.data.length} data points
        </p>
      </div>
    </div>
  );
};

export default ChartDisplay;