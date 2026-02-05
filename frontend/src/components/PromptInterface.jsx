import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wand2, Loader2, Sparkles, X } from 'lucide-react';

export default function PromptInterface({ onGenerate, loading }) {
  const [prompt, setPrompt] = useState('');
  const [showExamples, setShowExamples] = useState(false);
  const textareaRef = useRef(null);

  const examples = [
    "Design a bio-inspired robotic gripper for handling delicate biological samples with lattice infill for weight reduction.",
    "Build a 4-axis robot arm with 500mm reach, capable of lifting 2kg, using MG996R servos.",
    "Create a lightweight 2-DOF pan-tilt mechanism using 28BYJ-48 stepper motors.",
    "Generate a linear actuator with 100mm stroke, aluminum frame with 3D printed components."
  ];

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.max(120, Math.min(textarea.scrollHeight, 400));
      textarea.style.height = `${newHeight}px`;
    }
  }, [prompt]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim() && !loading) {
      onGenerate(prompt);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-20 group-focus-within:opacity-40 transition duration-1000"></div>

        <div className="relative bg-[#121216] border border-slate-800 rounded-2xl overflow-hidden focus-within:border-blue-500/50 transition-all">
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your robotic device... (e.g. 'Design a 3-DOF arm for biology')"
            className="w-full p-6 bg-transparent text-slate-100 placeholder:text-slate-500 resize-none outline-none min-h-[120px] text-lg leading-relaxed"
            disabled={loading}
          />

          <div className="flex items-center justify-between px-6 py-4 bg-slate-900/50 border-t border-slate-800">
            <div className="flex gap-4">
               <button
                type="button"
                onClick={() => setShowExamples(true)}
                className="text-xs font-bold uppercase tracking-widest text-slate-500 hover:text-blue-400 transition-colors flex items-center gap-2"
               >
                 <Sparkles size={14} />
                 Examples
               </button>
            </div>

            <button
              type="submit"
              disabled={loading || !prompt.trim()}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-600/20 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="animate-spin" size={18} />
                  Aurora is Thinking...
                </>
              ) : (
                <>
                  <Wand2 size={18} />
                  Generate Design
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      <AnimatePresence>
        {showExamples && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm"
          >
            <div className="bg-[#121216] border border-slate-800 w-full max-w-xl rounded-3xl p-8 shadow-2xl relative">
              <button
                onClick={() => setShowExamples(false)}
                className="absolute top-6 right-6 text-slate-500 hover:text-white"
              >
                <X size={24} />
              </button>

              <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Sparkles className="text-blue-500" />
                Inspiration
              </h3>

              <div className="flex flex-col gap-3">
                {examples.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setPrompt(ex);
                      setShowExamples(false);
                    }}
                    className="text-left p-4 rounded-2xl bg-slate-900 border border-slate-800 hover:border-blue-500/50 hover:bg-slate-800 transition-all text-sm text-slate-300 leading-relaxed"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function RefreshCw({ className, size }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
            <path d="M21 3v5h-5" />
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
            <path d="M3 21v-5h5" />
        </svg>
    )
}
