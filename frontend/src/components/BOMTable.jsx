import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, ExternalLink, Package, DollarSign, TrendingUp, AlertTriangle, CheckCircle, ChevronDown, ListFilter } from 'lucide-react';

export default function BOMTable({ bom }) {
  const [sortBy, setSortBy] = useState('category');
  const [sortOrder, setSortOrder] = useState('asc');
  const [filterCategory, setFilterCategory] = useState('all');

  if (!bom || !bom.items) {
    return (
      <div className="bg-[#121216] border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
        <Package size={48} className="mx-auto mb-4 opacity-20" />
        <p>No component sourcing data available yet.</p>
      </div>
    );
  }

  const categories = ['all', ...new Set(bom.items.map(item => item.category))];
  
  const filteredItems = filterCategory === 'all' 
    ? bom.items 
    : bom.items.filter(item => item.category === filterCategory);

  const sortedItems = [...filteredItems].sort((a, b) => {
    let aVal = a[sortBy];
    let bVal = b[sortBy];
    
    if (typeof aVal === 'string') {
      return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
  });

  return (
    <div className="bg-[#121216] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div className="p-6 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
         <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Package size={20} className="text-blue-500" />
              Bill of Materials
            </h2>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Real-time Sourcing</p>
         </div>
         <div className="flex gap-2">
            <button className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 transition-colors">
              <Download size={18} />
            </button>
         </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
           <SummaryStat label="Items" value={bom.summary.item_count} icon={<Package size={14}/>} />
           <SummaryStat label="Subtotal" value={`$${bom.summary.subtotal_usd.toFixed(2)}`} icon={<DollarSign size={14}/>} />
           <SummaryStat label="Total Cost" value={`$${bom.summary.total_usd.toFixed(2)}`} icon={<TrendingUp size={14}/>} highlight />
           <SummaryStat label="Est. Weight" value={`${bom.summary.total_weight_g.toFixed(0)}g`} icon={<BoxIcon size={14}/>} />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="pb-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Category</th>
                <th className="pb-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Component</th>
                <th className="pb-4 text-[10px] font-black uppercase tracking-widest text-slate-500 text-right">Price</th>
                <th className="pb-4 text-[10px] font-black uppercase tracking-widest text-slate-500 text-center">Qty</th>
                <th className="pb-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {sortedItems.map((item, i) => (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="group hover:bg-slate-800/20"
                >
                  <td className="py-4">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-bold border border-slate-700">
                      {item.category}
                    </span>
                  </td>
                  <td className="py-4">
                    <div className="flex flex-col">
                      <span className="text-sm font-bold text-slate-200">{item.item}</span>
                      <span className="text-[10px] font-mono text-slate-500 uppercase">{item.supplier}</span>
                    </div>
                  </td>
                  <td className="py-4 text-right">
                    <span className="text-sm font-mono-tabular font-bold text-slate-200">${item.unit_cost_usd.toFixed(2)}</span>
                  </td>
                  <td className="py-4 text-center">
                    <span className="text-xs font-bold text-blue-500">{item.quantity}</span>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-green-500">
                       <CheckCircle size={12} />
                       IN STOCK
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SummaryStat({ label, value, icon, highlight }) {
  return (
    <div className={`p-4 rounded-2xl border ${highlight ? 'bg-blue-600/10 border-blue-500/30' : 'bg-slate-900/50 border-slate-800'}`}>
      <div className="flex items-center gap-2 text-slate-500 mb-1">
        {icon}
        <span className="text-[10px] font-bold uppercase tracking-widest">{label}</span>
      </div>
      <div className={`text-xl font-black tabular-nums ${highlight ? 'text-blue-400' : 'text-slate-100'}`}>
        {value}
      </div>
    </div>
  );
}

function BoxIcon({ size, className }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
      <path d="m3.3 7 8.7 5 8.7-5" />
      <path d="M12 22V12" />
    </svg>
  );
}
