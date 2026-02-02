import React from 'react';
import './ProgressTracker.css';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

export default function ProgressTracker({ status }) {
  if (!status) return null;

  const steps = [
    { id: 'parsing', label: 'Parsing Prompt', progress: 10 },
    { id: 'validating', label: 'Validating Design', progress: 20 },
    { id: 'optimizing', label: 'Optimizing Parameters', progress: 30 },
    { id: 'generating_code', label: 'Generating Code', progress: 40 },
    { id: 'compiling', label: 'Compiling Geometry', progress: 70 },
    { id: 'calculating_bom', label: 'Calculating BOM', progress: 90 },
    { id: 'completed', label: 'Complete', progress: 100 }
  ];

  const currentStepIndex = steps.findIndex(step => step.id === status.status);
  const progress = status.progress || 0;

  return (
    <div className="progress-container">
      <div className="progress-header-section">
        <div className="progress-title-row">
          <h3 className="progress-title">Generating Design</h3>
          <span className="progress-percentage">{progress}%</span>
        </div>
        <div className="progress-bar-wrapper">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      <div className="progress-steps">
        {steps.map((step, idx) => {
          const isActive = idx === currentStepIndex;
          const isComplete = idx < currentStepIndex;
          const isFailed = status.status === 'failed' && idx === currentStepIndex;

          return (
            <div
              key={step.id}
              className={`progress-step ${
                isActive ? 'step-active' :
                isComplete ? 'step-complete' :
                isFailed ? 'step-failed' :
                'step-pending'
              }`}
            >
              <div className="step-icon">
                {isComplete && <CheckCircle size={20} />}
                {isActive && !isFailed && <Loader2 size={20} className="spin-animation" />}
                {isFailed && <AlertCircle size={20} />}
                {!isActive && !isComplete && !isFailed && (
                  <div className="step-dot"></div>
                )}
              </div>
              <span className="step-label">{step.label}</span>
            </div>
          );
        })}
      </div>

      {status.current_step && (
        <div className="progress-status">
          <p className="status-text">{status.current_step}</p>
        </div>
      )}
    </div>
  );
}