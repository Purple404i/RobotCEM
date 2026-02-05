import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, AlertTriangle, CheckCircle, Info, Box, Ruler, Weight, ShieldCheck } from 'lucide-react';

export default function SpecificationPanel({ spec, validation }) {
  const [expandedSections, setExpandedSections] = useState({
    type: true,
    dimensions: true,
    loads: true,
    materials: true,
    components: true
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const Section = ({ title, icon, children, section }) => (
    <div className="border-b border-slate-800 last:border-0">
      <button
        onClick={() => toggleSection(section)}
        className="w-full py-4 flex items-center justify-between hover:bg-slate-800/30 transition-colors px-4 rounded-lg group"
      >
        <div className="flex items-center gap-3">
          <div className="text-slate-500 group-hover:text-blue-400 transition-colors">
            {icon}
          </div>
          <h3 className="font-bold text-sm tracking-tight text-slate-300">{title}</h3>
        </div>
        {expandedSections[section] ? <ChevronDown size={16} className="text-slate-600" /> : <ChevronRight size={16} className="text-slate-600" />}
      </button>
      <AnimatePresence>
        {expandedSections[section] && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-0">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  return (
    <div className="bg-[#121216] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
        <h2 className="font-bold text-slate-100 flex items-center gap-2">
          <ShieldCheck size={18} className="text-blue-500" />
          Technical Specs
        </h2>
        {validation?.is_valid && (
           <span className="text-[10px] font-black uppercase tracking-widest text-green-500 bg-green-500/10 px-2 py-0.5 rounded">Verified</span>
        )}
      </div>

      <div className="flex flex-col">
        <Section title="Device & Process" icon={<Box size={16} />} section="type">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Classification</p>
              <p className="text-sm font-semibold text-slate-200 capitalize">{spec.device_type.replace('_', ' ')}</p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Manufacturing</p>
              <p className="text-sm font-semibold text-slate-200">{spec.manufacturing}</p>
            </div>
          </div>
        </Section>

        <Section title="Dimensions" icon={<Ruler size={16} />} section="dimensions">
          <div className="grid grid-cols-2 gap-y-4 gap-x-6">
            {Object.entries(spec.dimensions || {}).map(([key, value]) => (
              <div key={key} className="space-y-1">
                <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">{key.replace('_', ' ')}</p>
                <p className="text-sm font-semibold text-slate-200">{value} <span className="text-[10px] text-slate-500 font-normal">mm</span></p>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Loads & Dynamics" icon={<Weight size={16} />} section="loads">
          <div className="grid grid-cols-2 gap-y-4 gap-x-6">
            {Object.entries(spec.loads || {}).map(([key, value]) => (
              <div key={key} className="space-y-1">
                <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">{key.replace('_', ' ')}</p>
                <p className="text-sm font-semibold text-slate-200">
                  {value} <span className="text-[10px] text-slate-500 font-normal">{key.includes('kg') ? 'kg' : key.includes('torque') ? 'N·m' : 'N'}</span>
                </p>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Bill of Materials" icon={<Info size={16} />} section="components">
          {spec.components && spec.components.length > 0 ? (
            <div className="flex flex-col gap-2">
              {spec.components.map((component, idx) => (
                <div key={idx} className="p-3 bg-slate-900 rounded-xl border border-slate-800 flex justify-between items-center group">
                  <div>
                    <p className="text-sm font-bold text-slate-200">{component.name || component.type}</p>
                    {component.mpn && (
                      <p className="text-[10px] font-mono text-slate-500 uppercase tracking-tighter">PN: {component.mpn}</p>
                    )}
                  </div>
                  <span className="text-xs font-black text-blue-500 bg-blue-500/10 px-2 py-1 rounded-lg">
                    ×{component.quantity}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No external components required.</p>
          )}
        </Section>
      </div>
    </div>
  );
}
