import React, { useState, useEffect } from 'react';
import './App.css';
import PromptInterface from './components/PromptInterface';
import STLViewer3D from './components/STLViewer3D';
import BOMTable from './components/BOMTable';
import ProgressTracker from './components/ProgressTracker';
import SpecificationPanel from './components/SpecificationPanel';
import { AlertCircle, CheckCircle, Loader2, Sparkles } from 'lucide-react';

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
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-icon">
              <Sparkles size={20} strokeWidth={2} />
            </div>
            <div className="logo-text">
              <h1>Robot CEM Studio</h1>
              <p>Computational Engineering for Robotics</p>
            </div>
          </div>
          {status?.status === 'completed' && (
            <button onClick={handleReset} className="new-design-btn">
              New Design
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="content-wrapper">
          {/* Error Display */}
          {error && (
            <div className="error-banner">
              <AlertCircle size={20} />
              <div className="error-content">
                <h3>Generation Failed</h3>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* Prompt Interface */}
          {!status && !loading && (
            <div className="prompt-section">
              <div className="hero-content">
                <h2 className="hero-title">Design Your Robot</h2>
                <p className="hero-description">
                  Describe your device and we'll generate the complete design with 3D models, BOM, and cost estimates
                </p>
              </div>
              <PromptInterface onGenerate={handleGenerate} loading={loading} />
            </div>
          )}

          {/* Progress Tracker */}
          {loading && status && (
            <div className="progress-section">
              <ProgressTracker status={status} />
            </div>
          )}

          {/* Results */}
          {status?.status === 'completed' && (
            <div className="results-section">
              {/* Success Message */}
              <div className="success-banner">
                <CheckCircle size={24} />
                <div className="success-content">
                  <h3>Design Generated Successfully!</h3>
                  <p>Your robot design is ready for review and export.</p>
                </div>
              </div>

              {/* Specification Panel */}
              {status.specification && (
                <div className="spec-container">
                  <SpecificationPanel 
                    spec={status.specification} 
                    validation={status.validation}
                  />
                </div>
              )}

              {/* 3D Viewer */}
              {status.stl_url && (
                <div className="viewer-container">
                  <div className="viewer-header">
                    <h2>3D Model Preview</h2>
                  </div>
                  <div className="viewer-canvas">
                    <STLViewer3D stlUrl={`${API_BASE}${status.stl_url}`} />
                  </div>
                </div>
              )}

              {/* Bill of Materials */}
              {status.bom && (
                <div className="bom-container">
                  <BOMTable bom={status.bom} />
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Powered by LEAP71 PicoGK, HuggingFace Transformers, and Three.js</p>
        <p>© 2025 Robot CEM Studio</p>
      </footer>
    </div>
  );
}