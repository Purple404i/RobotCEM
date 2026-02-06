import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import PromptInterface from './components/PromptInterface';
import STLViewer3D from './components/STLViewer3D';
import BOMTable from './components/BOMTable';
import ProgressTracker from './components/ProgressTracker';
import SpecificationPanel from './components/SpecificationPanel';
import BrowserPanel from './components/BrowserPanel';
import {
  AlertCircle, CheckCircle, Sparkles, LayoutDashboard,
  Database, Box, PlayCircle, RefreshCw, Search,
  ChevronLeft, ChevronRight, MessageSquare
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('design');
  const [viewerMode, setViewerMode] = useState('threejs');
  const [isBrowsing, setIsBrowsing] = useState(false);
  const [droppedParts, setDroppedParts] = useState([]);

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
    setActiveTab('design'); // Keep on design to see the layout shift

    // If there are dropped parts, append them to the prompt
    let finalPrompt = prompt;
    if (droppedParts.length > 0) {
        const partsList = droppedParts.map(p => `- ${p.name} (MPN: ${p.mpn}, Price: $${p.price})`).join('\n');
        finalPrompt += `\n\nPlease incorporate these components into the design:\n${partsList}`;
    }

    try {
      const response = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: finalPrompt })
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

  const handleDrop = (e) => {
    e.preventDefault();
    try {
        const data = JSON.parse(e.dataTransfer.getData('application/json'));
        if (data.type === 'component') {
            setDroppedParts(prev => [...prev, data]);
            // You could also trigger a notification or small animation here
        }
    } catch (err) {
        console.error("Drop handling failed", err);
    }
  };

  const handleReset = () => {
    setJobId(null);
    setStatus(null);
    setLoading(false);
    setError(null);
    setDroppedParts([]);
    setActiveTab('design');
  };

  const isSimulating = !!jobId && status?.status !== 'failed';

  return (
    <div className="app-container min-h-screen bg-[#0a0a0c] text-slate-200 flex overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="h-screen w-20 bg-[#121216] border-r border-slate-800 flex flex-col items-center py-8 z-50 flex-shrink-0">
        <div className="mb-12 text-blue-500">
          <Sparkles size={32} />
        </div>

        <nav className="flex flex-col gap-8">
          <NavButton active={activeTab === 'design'} onClick={() => setActiveTab('design')} icon={<LayoutDashboard size={24} />} label="Studio" />
          <NavButton active={isBrowsing} onClick={() => setIsBrowsing(!isBrowsing)} icon={<Search size={24} />} label="Browser" />
          <NavButton active={activeTab === 'library'} onClick={() => setActiveTab('library')} icon={<Database size={24} />} label="Library" />
        </nav>
      </aside>

      {/* Market Browser (Collapsible) */}
      <AnimatePresence>
        {isBrowsing && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 320, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="h-screen overflow-hidden flex-shrink-0"
          >
            <BrowserPanel apiBase={API_BASE} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Area */}
      <div className="flex-1 flex flex-col h-screen relative overflow-hidden">
        <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-[#0a0a0c]/80 backdrop-blur-md z-40">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
              RobotCEM Studio
            </h1>
            <span className="px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-widest">
              Aurora v1.1
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

        <main
            className="flex-1 relative overflow-hidden flex"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
        >
          {/* 3D Visualizer / Workspace (Center) */}
          <div className={`flex-1 transition-all duration-500 ${isSimulating ? 'mr-96' : ''}`}>
             <div className="h-full p-6">
                <AnimatePresence mode="wait">
                  {activeTab === 'design' && (
                    <motion.div
                      key="design-content"
                      className="h-full flex flex-col"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      {!status && !loading ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center">
                          <motion.div
                            initial={{ scale: 0.8 }}
                            animate={{ scale: 1 }}
                            className="w-24 h-24 rounded-full bg-blue-500/10 flex items-center justify-center mb-8 border border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.1)]"
                          >
                            <Sparkles size={48} className="text-blue-500" />
                          </motion.div>
                          <h2 className="text-4xl font-bold mb-4 tracking-tight text-white">Design with Aurora</h2>
                          <p className="text-slate-400 max-w-xl mb-12 text-lg">
                            Describe your robotic device. Aurora will handle engineering, sourcing, generation, and simulation.
                          </p>
                          <div className="w-full max-w-2xl">
                            <PromptInterface onGenerate={handleGenerate} loading={loading} droppedParts={droppedParts} />
                          </div>
                        </div>
                      ) : (
                        <div className="h-full flex flex-col gap-6">
                           <div className="flex-1 bg-[#121216] border border-slate-800 rounded-3xl overflow-hidden relative shadow-2xl">
                              <div className="absolute top-6 left-6 z-10 flex gap-2">
                                 <button
                                    onClick={() => setViewerMode('threejs')}
                                    className={`px-4 py-2 rounded-xl text-[10px] font-bold uppercase tracking-wider border transition-all backdrop-blur ${
                                      viewerMode === 'threejs'
                                        ? 'bg-blue-600 border-blue-500 text-white'
                                        : 'bg-slate-900/80 border-slate-700 text-slate-400 hover:text-white'
                                    }`}
                                 >
                                   Three.js Interactor
                                 </button>
                                 <button
                                    onClick={() => setViewerMode('blender')}
                                    className={`px-4 py-2 rounded-xl text-[10px] font-bold uppercase tracking-wider border transition-all backdrop-blur ${
                                      viewerMode === 'blender'
                                        ? 'bg-indigo-600 border-indigo-500 text-white'
                                        : 'bg-slate-900/80 border-slate-700 text-slate-400 hover:text-white'
                                    }`}
                                 >
                                   Blender Scientific Render
                                 </button>
                              </div>

                              {status?.stl_url ? (
                                <STLViewer3D
                                  stlUrl={`${API_BASE}${status.stl_url}`}
                                  mode={viewerMode}
                                  jobId={jobId}
                                  apiBase={API_BASE}
                                />
                              ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-4">
                                   <Box size={64} className="opacity-10 animate-pulse" />
                                   <div className="text-center">
                                      <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">{status?.current_step || 'Generating geometry...'}</p>
                                      <div className="w-48 h-1 bg-slate-800 rounded-full mt-4 overflow-hidden">
                                         <motion.div
                                            className="h-full bg-blue-500"
                                            initial={{ width: 0 }}
                                            animate={{ width: `${status?.progress || 0}%` }}
                                         />
                                      </div>
                                   </div>
                                </div>
                              )}
                           </div>

                           {!isSimulating && (
                              <div className="grid grid-cols-2 gap-6 h-64 overflow-y-auto custom-scrollbar">
                                {status?.specification && <SpecificationPanel spec={status.specification} validation={status.validation} />}
                                {status?.bom && <BOMTable bom={status.bom} />}
                              </div>
                           )}
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
             </div>
          </div>

          {/* Right Sidebar (Copilot Chat / Simulation Details) */}
          {isSimulating && (
          <aside
            className="absolute right-0 top-0 h-full w-96 bg-[#121216] border-l border-slate-800 p-6 z-30 shadow-2xl flex flex-col"
          >
            <div className="flex items-center gap-3 mb-6">
               <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
                  <MessageSquare size={18} />
               </div>
               <h3 className="font-bold text-white">Aurora Copilot</h3>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar space-y-6">
                {status?.scientific_analysis && (
                  <div className="bg-blue-500/5 border border-blue-500/20 rounded-2xl p-4">
                     <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-2 block">Live Analysis</span>
                     <p className="text-sm text-slate-300 italic leading-relaxed">
                       "{status.scientific_analysis.analysis}"
                     </p>
                  </div>
                )}

                {status?.simulation && (
                  <div className="space-y-4">
                     <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">Simulation Data</span>
                     <div className="grid grid-cols-2 gap-3">
                        <SimStat label="Physics Stability" value={status.simulation.fell_over ? 'FAILED' : 'PASSED'} color={status.simulation.fell_over ? 'text-red-400' : 'text-green-400'} />
                        <SimStat label="Settling Time" value={`${status.simulation.settling_time?.toFixed(2)}s`} />
                     </div>
                  </div>
                )}

                <div className="pt-6 mt-6 border-t border-slate-800">
                   <PromptInterface onGenerate={handleGenerate} loading={loading} mini />
                </div>
            </div>
          </aside>
          )}
        </main>
      </div>

      {/* Background decorations */}
      <div className="fixed top-0 right-0 -z-10 w-[800px] h-[800px] bg-blue-500/5 blur-[160px] rounded-full pointer-events-none"></div>
      <div className="fixed bottom-0 left-0 -z-10 w-[600px] h-[600px] bg-indigo-500/5 blur-[140px] rounded-full pointer-events-none"></div>
    </div>
  );
}

function NavButton({ active, icon, label, onClick }) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
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

function SimStat({ label, value, color = "text-white" }) {
  return (
    <div className="bg-slate-900 rounded-xl p-3 border border-slate-800">
      <span className="text-[9px] font-bold text-slate-500 uppercase block mb-1">{label}</span>
      <span className={`text-xs font-mono font-bold ${color}`}>{value}</span>
    </div>
  );
}
