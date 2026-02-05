import React, { useState } from 'react';
import { Send, Loader2, Plus, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function PromptInterface({ onGenerate, loading, droppedParts = [], mini = false }) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim() && !loading) {
      onGenerate(prompt);
      setPrompt('');
    }
  };

  return (
    <div className={`w-full ${mini ? '' : 'bg-[#121216]/50 border border-slate-800 p-2 rounded-2xl shadow-xl backdrop-blur-sm'}`}>
      {!mini && droppedParts.length > 0 && (
        <div className="px-4 py-2 flex flex-wrap gap-2 mb-2 border-b border-slate-800 pb-3">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest w-full mb-1">Attached Components</span>
          {droppedParts.map((part, idx) => (
            <div key={idx} className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-[10px] text-blue-400 flex items-center gap-2">
              {part.name}
              <Plus size={10} className="rotate-45 opacity-50" />
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="relative flex gap-2 p-1">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={mini ? "Ask Aurora to fix/edit..." : "Design a robotic arm with 3 degrees of freedom..."}
          className={`w-full bg-slate-900/50 text-slate-200 placeholder-slate-500 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all resize-none ${mini ? 'text-xs min-h-[80px]' : 'min-h-[100px] text-lg'}`}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          disabled={loading || !prompt.trim()}
          className={`absolute right-4 bottom-4 p-3 rounded-xl transition-all ${
            loading || !prompt.trim()
              ? 'bg-slate-800 text-slate-600'
              : 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-600/20'
          }`}
        >
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
        </button>
      </form>

      {!mini && (
        <div className="flex justify-between items-center px-4 py-3 text-[10px] text-slate-500 font-medium uppercase tracking-widest">
           <div className="flex gap-4">
              <button onClick={() => setPrompt("Design a hexapod robot for rough terrain")} className="hover:text-blue-400 transition-colors">Example: Hexapod</button>
              <button onClick={() => setPrompt("Create a 2-DOF camera gimbal")} className="hover:text-blue-400 transition-colors">Example: Gimbal</button>
           </div>
           <span>Aurora V1.1 Engineering Core</span>
        </div>
      )}
    </div>
  );
}
