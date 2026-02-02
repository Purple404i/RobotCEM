import React, { useState } from 'react';
import { ChevronDown, ChevronRight, AlertTriangle, CheckCircle, Info } from 'lucide-react';

export default function SpecificationPanel({ spec, validation }) {
  const [expandedSections, setExpandedSections] = useState({
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

  const Section = ({ title, children, section }) => (
    <div className="border-b border-gray-700 last:border-0">
      <button
        onClick={() => toggleSection(section)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-750 transition-colors"
      >
        <h3 className="font-semibold text-lg">{title}</h3>
        {expandedSections[section] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
      </button>
      {expandedSections[section] && (
        <div className="px-4 pb-4">
          {children}
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 p-4">
        <h2 className="text-xl font-bold">Design Specification</h2>
      </div>

      {/* Validation Status */}
      {validation && (
        <div className={`p-4 ${
          validation.is_valid ? 'bg-green-900 bg-opacity-20' : 'bg-yellow-900 bg-opacity-20'
        } border-b border-gray-700`}>
          <div className="flex items-start gap-3">
            {validation.is_valid ? (
              <CheckCircle className="text-green-500 flex-shrink-0 mt-1" size={20} />
            ) : (
              <AlertTriangle className="text-yellow-500 flex-shrink-0 mt-1" size={20} />
            )}
            <div className="flex-1">
              <h3 className="font-semibold mb-2">
                {validation.is_valid ? 'Design Validated' : 'Design Warnings'}
              </h3>
              
              {validation.warnings && validation.warnings.length > 0 && (
                <div className="space-y-1 mb-2">
                  {validation.warnings.map((warning, idx) => (
                    <p key={idx} className="text-sm text-yellow-200">• {warning}</p>
                  ))}
                </div>
              )}
              
              {validation.suggested_fixes && validation.suggested_fixes.length > 0 && (
                <div className="mt-3 p-3 bg-gray-900 bg-opacity-50 rounded">
                  <p className="text-sm font-semibold mb-2">Suggested Improvements:</p>
                  {validation.suggested_fixes.map((fix, idx) => (
                    <p key={idx} className="text-sm text-gray-300">• {fix}</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Specifications */}
      <div>
        <Section title="Device Type" section="type">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-400 mb-1">Type</p>
              <p className="font-medium capitalize">{spec.device_type.replace('_', ' ')}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Manufacturing</p>
              <p className="font-medium">{spec.manufacturing}</p>
            </div>
          </div>
        </Section>

        <Section title="Dimensions" section="dimensions">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(spec.dimensions || {}).map(([key, value]) => (
              <div key={key}>
                <p className="text-sm text-gray-400 mb-1 capitalize">{key.replace('_', ' ')}</p>
                <p className="font-medium">{value} mm</p>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Loads & Forces" section="loads">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(spec.loads || {}).map(([key, value]) => (
              <div key={key}>
                <p className="text-sm text-gray-400 mb-1 capitalize">{key.replace('_', ' ')}</p>
                <p className="font-medium">{value} {key.includes('kg') ? 'kg' : key.includes('torque') ? 'N·m' : 'N'}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Materials" section="materials">
          <div className="flex flex-wrap gap-2">
            {spec.materials && spec.materials.map((material, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-blue-600 bg-opacity-30 border border-blue-500 rounded-full text-sm"
              >
                {material}
              </span>
            ))}
          </div>
        </Section>

        <Section title="Components" section="components">
          {spec.components && spec.components.length > 0 ? (
            <div className="space-y-3">
              {spec.components.map((component, idx) => (
                <div key={idx} className="p-3 bg-gray-900 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{component.name || component.type}</p>
                      {component.mpn && (
                        <p className="text-sm text-gray-400 font-mono mt-1">MPN: {component.mpn}</p>
                      )}
                    </div>
                    <span className="px-2 py-1 bg-blue-600 rounded text-sm">
                      Qty: {component.quantity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No components specified</p>
          )}
        </Section>
      </div>
    </div>
  );
}