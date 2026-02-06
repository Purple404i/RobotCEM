import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function ProgressTracker({ status }) {
  if (!status) return null;

  const steps = [
    { id: 'parsing', label: 'Aurora Analysis' },
    { id: 'validating', label: 'Physics Validation' },
    { id: 'generating_code', label: 'Dynamic CAD Generation' },
    { id: 'compiling', label: 'PicoGK Execution' },
    { id: 'simulation', label: 'Blender Simulation' },
    { id: 'calculating_bom', label: 'Market Sourcing' },
    { id: 'completed', label: 'Design Ready' }
  ];

  const currentStepIndex = steps.findIndex(step => step.id === status.status);
  const progress = status.progress || 0;

  return (
    <div className="space-y-8">
      <div className="relative">
        <div className="flex justify-between items-end mb-3">
           <div className="space-y-1">
             <span className="text-[10px] font-bold uppercase tracking-widest text-blue-500">System Status</span>
             <h3 className="text-lg font-bold text-white">Interdisciplinary Design Workflow</h3>
           </div>
           <span className="text-2xl font-black text-blue-500 tabular-nums">{progress}%</span>
        </div>

        <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden border border-slate-700/50">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ type: "spring", stiffness: 50 }}
            className="h-full bg-gradient-to-r from-blue-600 to-indigo-500"
          />
        </div>
      </div>

      <div className="grid gap-3">
        {steps.map((step, idx) => {
          const isActive = idx === currentStepIndex;
          const isComplete = idx < currentStepIndex;
          const isFailed = status.status === 'failed' && idx === currentStepIndex;

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className={`flex items-center gap-4 p-4 rounded-2xl border transition-all duration-500 ${
                isActive
                  ? 'bg-blue-500/10 border-blue-500/30 ring-1 ring-blue-500/20'
                  : isComplete
                    ? 'bg-slate-900/40 border-slate-800 opacity-60'
                    : 'bg-transparent border-transparent opacity-30'
              }`}
            >
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                isComplete ? 'text-green-500' : isActive ? 'text-blue-500' : 'text-slate-600'
              }`}>
                {isComplete ? <CheckCircle size={20} /> :
                 isActive && !isFailed ? <Loader2 size={20} className="animate-spin" /> :
                 isFailed ? <AlertCircle size={20} className="text-red-500" /> :
                 <div className="w-2 h-2 rounded-full bg-current" />}
              </div>

              <div className="flex-grow">
                <span className={`text-sm font-bold tracking-tight ${
                  isActive ? 'text-white' : 'text-slate-400'
                }`}>
                  {step.label}
                </span>
                {isActive && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-[10px] text-blue-400 mt-0.5 font-medium"
                  >
                    {status.current_step || 'Processing...'}
                  </motion.p>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
