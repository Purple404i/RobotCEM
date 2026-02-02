import React from 'react';
import './progress.css';
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
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold">Generating Design</h3>
          <span className="text-2xl font-bold text-blue-400">{progress}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-cyan-500 h-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      <div className="space-y-3">
        {steps.map((step, idx) => {
          const isActive = idx === currentStepIndex;
          const isComplete = idx < currentStepIndex;
          const isFailed = status.status === 'failed' && idx === currentStepIndex;

          return (
            <div
              key={step.id}
              className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                isActive ? 'bg-blue-900 bg-opacity-30 border border-blue-500' :
                isComplete ? 'bg-green-900 bg-opacity-20' :
                isFailed ? 'bg-red-900 bg-opacity-20 border border-red-500' :
                'bg-gray-900 bg-opacity-50'
              }`}
            >
              {isComplete && <CheckCircle className="text-green-500" size={20} />}
              {isActive && !isFailed && <Loader2 className="text-blue-500 animate-spin" size={20} />}
              {isFailed && <AlertCircle className="text-red-500" size={20} />}
              {!isActive && !isComplete && !isFailed && (
                <div className="w-5 h-5 border-2 border-gray-600 rounded-full"></div>
              )}
              <span className={`font-medium ${
                isActive ? 'text-white' :
                isComplete ? 'text-green-400' :
                isFailed ? 'text-red-400' :
                'text-gray-500'
              }`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {status.current_step && (
        <div className="mt-4 p-3 bg-gray-900 rounded-lg">
          <p className="text-sm text-gray-400">{status.current_step}</p>
        </div>
      )}
    </div>
  );
}