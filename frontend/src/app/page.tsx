"use client";

import React, { useState } from 'react';
import FileUpload from '@/components/FileUpload';
import ChartDisplay from '@/components/ChartDisplay';

interface ChartSuggestion {
  type: string;
  title: string;
  x_axis?: string;
  y_axis?: string;
  explanation: string;
  data: any[];
}

interface UploadResponse {
  status: string;
  data_info: {
    columns: string[];
    row_count: number;
    column_count: number;
    sample_data: any[];
    column_types: Record<string, string>;
  };
  chart_suggestions: ChartSuggestion[];
}

export default function Home() {
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    setLoading(true);
    setError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      setUploadResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Data Visualizer
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your CSV or Excel files and get AI-powered chart suggestions 
            to visualize your data in meaningful ways.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <FileUpload onFileUpload={handleFileUpload} loading={loading} />

          {error && (
            <div className="mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              <h3 className="font-semibold">Error:</h3>
              <p>{error}</p>
            </div>
          )}

          {uploadResult && (
            <div className="mt-8">
              <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                  Dataset Information
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-blue-800">Rows</h3>
                    <p className="text-2xl font-bold text-blue-600">
                      {uploadResult.data_info.row_count.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-green-800">Columns</h3>
                    <p className="text-2xl font-bold text-green-600">
                      {uploadResult.data_info.column_count}
                    </p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-purple-800">Charts</h3>
                    <p className="text-2xl font-bold text-purple-600">
                      {uploadResult.chart_suggestions.length}
                    </p>
                  </div>
                </div>
                
                <div className="mb-4">
                  <h3 className="font-semibold text-gray-700 mb-2">Columns:</h3>
                  <div className="flex flex-wrap gap-2">
                    {uploadResult.data_info.columns.map((column, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-sm"
                      >
                        {column}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                  AI Chart Suggestions
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {uploadResult.chart_suggestions.map((suggestion, index) => (
                    <ChartDisplay
                      key={index}
                      suggestion={suggestion}
                      index={index}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}