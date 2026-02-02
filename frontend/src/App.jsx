import React, { useState, useEffect } from 'react';
import PromptInterface from './components/PromptInterface';
import STLViewer3D from './components/STLViewer3D';
import BOMTable from './components/BOMTable';
import ProgressTracker from './components/ProgressTracker';
import SpecificationPanel from './components/SpecificationPanel';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Poll for status updates
  useEffect(() => {
    if (!jobId || status?.status === 'completed' || status?.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/api/status/${jobId}`);
        const data = await response.json();
        setStatus(data);

        if (data.status === 'completed' || data.status === 'failed') {
          setLoading(false);
        }
      } catch (err) {
        console.error('Status poll error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, status]);

  const handleGenerate = async (prompt) => {
    setLoading(true);
    setError(null);
    setStatus(null);

    try {
      const response = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setJobId(data.job_id);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleReset = () => {
    setJobId(null);
    setStatus(null);
    setLoading(false);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900 bg-opacity-50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg"></div>
              <div>
                <h1 className="text-2xl font-bold">Robot CEM Studio</h1>
                <p className="text-sm text-gray-400">Computational Engineering for Robotics</p>
              </div>
            </div>
            {status?.status === 'completed' && (
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                New Design
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-900 bg-opacity-20 border border-red-500 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="text-red-500 flex-shrink-0 mt-1" size={20} />
            <div>
              <h3 className="font-semibold mb-1">Generation Failed</h3>
              <p className="text-sm text-gray-300">{error}</p>
            </div>
          </div>
        )}

        {/* Prompt Interface */}
        {!status && !loading && (
          <div className="mb-8">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Design Your Robot
              </h2>
              <p className="text-xl text-gray-400">
                Describe your device and we'll generate the complete design with 3D models, BOM, and cost estimates
              </p>
            </div>
            <PromptInterface onGenerate={handleGenerate} loading={loading} />
          </div>
        )}

        {/* Progress Tracker */}
        {loading && status && (
          <div className="mb-8">
            <ProgressTracker status={status} />
          </div>
        )}

        {/* Results */}
        {status?.status === 'completed' && (
          <div className="space-y-8">
            {/* Success Message */}
            <div className="bg-green-900 bg-opacity-20 border border-green-500 rounded-lg p-4 flex items-center gap-3">
              <CheckCircle className="text-green-500" size={24} />
              <div>
                <h3 className="font-semibold">Design Generated Successfully!</h3>
                <p className="text-sm text-gray-300">Your robot design is ready for review and export.</p>
              </div>
            </div>

            {/* Specification Panel */}
            {status.specification && (
              <SpecificationPanel 
                spec={status.specification} 
                validation={status.validation}
              />
            )}

            {/* 3D Viewer */}
            {status.stl_url && (
              <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-600 to-cyan-600 p-4">
                  <h2 className="text-xl font-bold">3D Model Preview</h2>
                </div>
                <div className="h-[600px]">
                  <STLViewer3D stlUrl={`${API_BASE}${status.stl_url}`} />
                </div>
              </div>
            )}

            {/* Bill of Materials */}
            {status.bom && (
              <BOMTable bom={status.bom} />
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-700 bg-gray-900 mt-16">
        <div className="container mx-auto px-6 py-8">
          <div className="text-center text-gray-400 text-sm">
            <p>Powered by LEAP71 PicoGK, Anthropic Claude, and Three.js</p>
            <p className="mt-2">© 2025 Robot CEM Studio</p>
          </div>
        </div>
      </footer>
    </div>
  );
}