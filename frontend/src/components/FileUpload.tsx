"use client";

import React, { useCallback, useState } from 'react';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
  loading: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload, loading }) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        onFileUpload(file);
      }
    }
  }, [onFileUpload]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        onFileUpload(file);
      }
    }
  }, [onFileUpload]);

  const validateFile = (file: File): boolean => {
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    
    const validExtensions = ['.csv', '.xls', '.xlsx'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
      alert('Please upload a CSV or Excel file (.csv, .xls, .xlsx)');
      return false;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      alert('File size must be less than 10MB');
      return false;
    }
    
    return true;
  };

  return (
    <div className="w-full">
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-200 ${
          dragActive
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 bg-white hover:border-gray-400'
        } ${loading ? 'pointer-events-none opacity-50' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".csv,.xls,.xlsx"
          onChange={handleChange}
          disabled={loading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          
          {loading ? (
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3"></div>
              <p className="text-lg font-medium text-gray-700">
                Processing your file...
              </p>
              <p className="text-sm text-gray-500">
                Analyzing data and generating chart suggestions
              </p>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-lg font-medium text-gray-700 mb-2">
                Drop your CSV or Excel file here
              </p>
              <p className="text-sm text-gray-500 mb-4">
                or click to browse files
              </p>
              <div className="flex items-center justify-center space-x-2 text-xs text-gray-400">
                <span>Supported formats:</span>
                <span className="bg-gray-100 px-2 py-1 rounded">.csv</span>
                <span className="bg-gray-100 px-2 py-1 rounded">.xls</span>
                <span className="bg-gray-100 px-2 py-1 rounded">.xlsx</span>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Maximum file size: 10MB
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUpload;