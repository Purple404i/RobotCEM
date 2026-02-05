import React, { useState } from 'react';
import { Search, ExternalLink, Package, Loader2, GripVertical, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function BrowserPanel({ apiBase, onDragStart }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/api/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Search failed');
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#121216] border-r border-slate-800 w-80">
      <div className="p-4 border-b border-slate-800">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
          <Search size={14} />
          Market Browser
        </h3>
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search components..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg py-2 pl-3 pr-10 text-sm focus:outline-none focus:border-blue-500 transition-colors"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-blue-400 transition-colors"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          </button>
        </form>
      </div>

      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400 flex items-center gap-2 mb-4"
            >
              <AlertCircle size={14} />
              {error}
            </motion.div>
          )}

          {results.length > 0 ? (
            results.map((item, idx) => (
              <ResultCard key={idx} item={item} onDragStart={onDragStart} />
            ))
          ) : !loading && (
            <div className="flex flex-col items-center justify-center h-40 text-slate-600">
              <Package size={32} className="mb-2 opacity-20" />
              <p className="text-xs">Search for parts like "MG996R servo"</p>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function ResultCard({ item, onDragStart }) {
  const handleDragStart = (e) => {
    e.dataTransfer.setData('application/json', JSON.stringify({
        type: 'component',
        name: item.title,
        mpn: item.mpn,
        price: item.price_usd,
        url: item.url
    }));
    if (onDragStart) onDragStart(item);
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      draggable
      onDragStart={handleDragStart}
      className="group relative bg-slate-900/50 border border-slate-800 rounded-xl p-3 mb-3 hover:border-blue-500/50 hover:bg-slate-900 transition-all cursor-grab active:cursor-grabbing"
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-xs font-bold text-slate-200 line-clamp-2 pr-4">{item.title}</h4>
        <div className="text-slate-600 group-hover:text-blue-500 transition-colors">
          <GripVertical size={14} />
        </div>
      </div>

      {item.price_usd && (
        <div className="text-sm font-mono text-blue-400 mb-2">
          ${item.price_usd.toFixed(2)}
        </div>
      )}

      <div className="flex flex-wrap gap-2 mb-3">
        {item.mpn && (
          <span className="px-2 py-0.5 bg-slate-800 text-slate-400 text-[10px] rounded uppercase font-bold">
            {item.mpn}
          </span>
        )}
        {item.availability === 'In Stock' && (
          <span className="px-2 py-0.5 bg-green-500/10 text-green-500 text-[10px] rounded font-bold">
            In Stock
          </span>
        )}
      </div>

      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-[10px] text-slate-500 hover:text-white flex items-center gap-1 transition-colors"
        onClick={(e) => e.stopPropagation()}
      >
        View on Market <ExternalLink size={10} />
      </a>
    </motion.div>
  );
}
