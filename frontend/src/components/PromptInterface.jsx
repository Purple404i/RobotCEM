import React, { useState, useRef, useEffect } from 'react';
import { Wand2, Loader2 } from 'lucide-react';

export default function PromptInterface({ onGenerate, loading }) {
  const [prompt, setPrompt] = useState('');
  const [showExamples, setShowExamples] = useState(false);
  const textareaRef = useRef(null);

  const examples = [
    "Build a 4-axis robot arm with 200mm reach, capable of lifting 500g, using MG996R servos, 3D printable in PLA",
    "Design a parallel jaw gripper with 40mm grip range, printed in PETG, for picking up cylindrical objects",
    "Create a 2-DOF pan-tilt mechanism for a camera, using 28BYJ-48 stepper motors, lightweight design",
    "Generate a linear actuator with 100mm stroke, lead screw driven, aluminum frame with 3D printed components"
  ];

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      
      // Calculate new height (min 150px, max 400px)
      const newHeight = Math.max(150, Math.min(textarea.scrollHeight, 400));
      textarea.style.height = `${newHeight}px`;
    }
  }, [prompt]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim() && !loading) {
      onGenerate(prompt);
    }
  };

  const useExample = (example) => {
    setPrompt(example);
    setShowExamples(false);
  };

  const handleTextareaChange = (e) => {
    setPrompt(e.target.value);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={handleTextareaChange}
            placeholder="Describe your device in detail: dimensions, loads, materials, components..."
            className="w-full p-4 pr-12 border-2 border-gray-700 rounded-lg bg-gray-800 text-white resize-y focus:border-blue-500 focus:outline-none transition-colors min-h-[150px] max-h-[400px]"
            style={{ 
              height: '150px',
              overflow: 'auto'
            }}
            disabled={loading}
          />
          <button
            type="button"
            onClick={() => setShowExamples(!showExamples)}
            className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
            title="Show examples"
          >
            <Wand2 size={20} />
          </button>
        </div>

        {showExamples && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-2">
            <p className="text-sm text-gray-400 mb-3">Example prompts:</p>
            {examples.map((example, i) => (
              <button
                key={i}
                type="button"
                onClick={() => useExample(example)}
                className="w-full text-left p-3 bg-gray-700 hover:bg-gray-600 rounded transition-colors text-sm"
              >
                {example}
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-400">
            {prompt.length} / 2000 characters
          </div>
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 disabled:from-gray-600 disabled:to-gray-600 text-white font-semibold rounded-lg transition-all duration-200 flex items-center gap-2 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Generating...
              </>
            ) : (
              <>
                <Wand2 size={20} />
                Generate Design
              </>
            )}
          </button>
        </div>
      </form>

      {loading && (
        <div className="mt-6 bg-gray-800 border border-blue-500 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <Loader2 className="animate-spin text-blue-500" size={24} />
            <span className="font-semibold">Generating your design...</span>
          </div>
          <p className="text-sm text-gray-400">
            This may take 1-3 minutes. We're parsing your prompt, validating physics, generating geometry, and calculating costs.
          </p>
        </div>
      )}
    </div>
  );
}