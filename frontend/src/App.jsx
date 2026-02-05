import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import PromptInterface from './components/PromptInterface';
import STLViewer3D from './components/STLViewer3D';
import BOMTable from './components/BOMTable';
import ProgressTracker from './components/ProgressTracker';
import SpecificationPanel from './components/SpecificationPanel';
import { AlertCircle, CheckCircle, Sparkles, LayoutDashboard, Database, Box, PlayCircle, RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('design');
  const [viewerMode, setViewerMode] = useState('threejs');

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
    setActiveTab('status');

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
    setActiveTab('design');
  };

  return (
    <div className="app-container min-h-screen bg-[#0a0a0c] text-slate-200 overflow-x-hidden">
      {/* Sidebar Navigation */}
      <aside className="fixed left-0 top-0 h-full w-20 bg-[#121216] border-r border-slate-800 flex flex-col items-center py-8 z-50">
        <div className="mb-12 text-blue-500">
          <Sparkles size={32} />
        </div>

        <nav className="flex flex-col gap-8">
          <NavButton active={activeTab === 'design'} onClick={() => setActiveTab('design')} icon={<LayoutDashboard size={24} />} label="Studio" />
          <NavButton active={activeTab === 'status'} onClick={() => setActiveTab('status')} icon={<RefreshCw size={24} />} label="Workflow" />
          <NavButton active={activeTab === 'library'} onClick={() => setActiveTab('library')} icon={<Database size={24} />} label="Library" />
        </nav>
      </aside>

      {/* Main Content */}
      <main className="pl-20">
        <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-[#0a0a0c]/80 backdrop-blur-md sticky top-0 z-40">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
              RobotCEM Studio
            </h1>
            <span className="px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-widest">
              Aurora v1.0
            </span>
          </div>

          <div className="flex items-center gap-4">
            {status?.status === 'completed' && (
              <button onClick={handleReset} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-500/20">
                New Design
              </button>
            )}
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs">
              JD
            </div>
          </div>
        </header>

        <div className="p-8 max-w-7xl mx-auto">
          <AnimatePresence mode="wait">
            {activeTab === 'design' && (
              <motion.div
                key="design"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
              >
                {!status && !loading ? (
                  <div className="py-20 flex flex-col items-center text-center">
                    <motion.div
                      initial={{ scale: 0.8 }}
                      animate={{ scale: 1 }}
                      transition={{
                        repeat: Infinity,
                        repeatType: "reverse",
                        duration: 3
                      }}
                      className="w-24 h-24 rounded-full bg-blue-500/10 flex items-center justify-center mb-8 border border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.1)]"
                    >
                      <Sparkles size={48} className="text-blue-500" />
                    </motion.div>
                    <h2 className="text-4xl font-bold mb-4 tracking-tight">Design with Interdisciplinary AI</h2>
                    <p className="text-slate-400 max-w-2xl mb-12 text-lg">
                      Describe your robotic device. Aurora will handle the engineering, sourcing, 3D generation, and physics simulation.
                    </p>
                    <div className="w-full max-w-3xl">
                      <PromptInterface onGenerate={handleGenerate} loading={loading} />
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Left Column: Result Details */}
                    <div className="lg:col-span-4 flex flex-col gap-6">
                      {status?.status === 'completed' && (
                        <motion.div
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 flex items-center gap-4"
                        >
                          <CheckCircle className="text-green-500" size={24} />
                          <div>
                            <h4 className="font-bold text-green-500">Design Validated</h4>
                            <p className="text-xs text-green-500/70">Simulation passed with scientific accuracy.</p>
                          </div>
                        </motion.div>
                      )}

                      {status?.specification && (
                        <SpecificationPanel spec={status.specification} validation={status.validation} />
                      )}

                      {status?.bom && (
                        <BOMTable bom={status.bom} />
                      )}
                    </div>

                    {/* Right Column: Visualizer */}
                    <div className="lg:col-span-8">
                      {status?.stl_url ? (
                        <div className="bg-[#121216] border border-slate-800 rounded-2xl overflow-hidden h-[600px] shadow-2xl relative">
                          <div className="absolute top-4 left-4 z-10 flex gap-2">
                             <div className="px-3 py-1 bg-slate-900/80 backdrop-blur rounded-full text-[10px] font-bold uppercase tracking-wider border border-slate-700">
                               PicoGK Geometry
                             </div>
                             {status.simulation && (
                               <div className="px-3 py-1 bg-blue-500/20 text-blue-400 backdrop-blur rounded-full text-[10px] font-bold uppercase tracking-wider border border-blue-500/30">
                                 Blender Simulated
                               </div>
                             )}
                             <button
                                onClick={() => setViewerMode(viewerMode === 'threejs' ? 'blender' : 'threejs')}
                                className="px-3 py-1 bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30 backdrop-blur rounded-full text-[10px] font-bold uppercase tracking-wider border border-indigo-500/30 transition-all"
                             >
                               Switch to {viewerMode === 'threejs' ? 'Blender Render' : 'Three.js View'}
                             </button>
                          </div>
                          <STLViewer3D
                            stlUrl={`${API_BASE}${status.stl_url}`}
                            mode={viewerMode}
                            jobId={jobId}
                            apiBase={API_BASE}
                          />
                        </div>
                      ) : (
                        <div className="bg-[#121216] border border-slate-800 rounded-2xl h-[600px] flex flex-col items-center justify-center text-slate-500 gap-4">
                           <Box size={48} className="opacity-20" />
                           <p>Awaiting geometry generation...</p>
                        </div>
                      )}

                      {status?.scientific_analysis && (
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="mt-6 bg-[#121216] border border-blue-500/20 rounded-2xl p-6"
                        >
                          <div className="flex items-center gap-2 mb-4">
                            <Sparkles size={18} className="text-blue-400" />
                            <h3 className="font-bold text-slate-100">Aurora Scientific Analysis</h3>
                          </div>
                          <p className="text-sm text-slate-400 leading-relaxed italic">
                            "{status.scientific_analysis.analysis}"
                          </p>
                        </motion.div>
                      )}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'status' && (
              <motion.div
                key="status"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="max-w-2xl mx-auto"
              >
                {status || loading ? (
                  <div className="bg-[#121216] border border-slate-800 rounded-2xl p-8 shadow-xl">
                    <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
                      <RefreshCw className={loading ? 'animate-spin text-blue-500' : 'text-slate-400'} size={24} />
                      Design Workflow
                    </h2>
                    <ProgressTracker status={status} />
                  </div>
                ) : (
                  <div className="text-center py-20 bg-[#121216] border border-dashed border-slate-800 rounded-2xl">
                    <PlayCircle size={48} className="mx-auto mb-4 text-slate-700" />
                    <p className="text-slate-500">No active workflow. Start a design to see progress.</p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Background elements */}
      <div className="fixed top-0 right-0 -z-10 w-[500px] h-[500px] bg-blue-500/5 blur-[120px] rounded-full"></div>
      <div className="fixed bottom-0 left-0 -z-10 w-[400px] h-[400px] bg-indigo-500/5 blur-[100px] rounded-full"></div>
    </div>
  );
}

function NavButton({ active, icon, label, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`group relative p-3 rounded-xl transition-all duration-300 ${
        active
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
          : 'bg-transparent text-slate-500 hover:bg-slate-800'
      }`}
    >
      {icon}
      <span className="absolute left-full ml-4 px-2 py-1 bg-slate-800 text-white text-[10px] font-bold rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none uppercase tracking-widest z-[100]">
        {label}
      </span>
      {active && (
        <motion.div
          layoutId="activeNav"
          className="absolute -right-1 top-1/2 -translate-y-1/2 w-1 h-6 bg-blue-400 rounded-full"
        />
      )}
    </button>
  );
}
