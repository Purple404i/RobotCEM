import React, { useState } from 'react';
import './SpecificationPanel.css';
import { ChevronDown, ChevronRight, AlertTriangle, CheckCircle, Info } from 'lucide-react';

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

  const Section = ({ title, children, section }) => (
    <div className="spec-section">
      <button
        onClick={() => toggleSection(section)}
        className="spec-section-header"
      >
        <h3 className="spec-section-title">{title}</h3>
        {expandedSections[section] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
      </button>
      {expandedSections[section] && (
        <div className="spec-section-content">
          {children}
        </div>
      )}
    </div>
  );

  return (
    <div className="spec-panel">
      <div className="spec-header">
        <h2 className="spec-header-title">Design Specification</h2>
      </div>

      {/* Validation Status */}
      {validation && (
        <div className={`spec-validation ${validation.is_valid ? 'validation-success' : 'validation-warning'}`}>
          <div className="validation-icon">
            {validation.is_valid ? (
              <CheckCircle size={20} />
            ) : (
              <AlertTriangle size={20} />
            )}
          </div>
          <div className="validation-content">
            <h3 className="validation-title">
              {validation.is_valid ? 'Design Validated' : 'Design Warnings'}
            </h3>
            
            {validation.warnings && validation.warnings.length > 0 && (
              <div className="validation-warnings">
                {validation.warnings.map((warning, idx) => (
                  <p key={idx} className="warning-item">• {warning}</p>
                ))}
              </div>
            )}
            
            {validation.suggested_fixes && validation.suggested_fixes.length > 0 && (
              <div className="validation-fixes">
                <p className="fixes-title">Suggested Improvements:</p>
                {validation.suggested_fixes.map((fix, idx) => (
                  <p key={idx} className="fix-item">• {fix}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Specifications */}
      <div className="spec-sections">
        <Section title="Device Type" section="type">
          <div className="spec-grid spec-grid-2">
            <div className="spec-item">
              <p className="spec-label">Type</p>
              <p className="spec-value">{spec.device_type.replace('_', ' ')}</p>
            </div>
            <div className="spec-item">
              <p className="spec-label">Manufacturing</p>
              <p className="spec-value">{spec.manufacturing}</p>
            </div>
          </div>
        </Section>

        <Section title="Dimensions" section="dimensions">
          <div className="spec-grid spec-grid-3">
            {Object.entries(spec.dimensions || {}).map(([key, value]) => (
              <div key={key} className="spec-item">
                <p className="spec-label">{key.replace('_', ' ')}</p>
                <p className="spec-value">{value} mm</p>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Loads & Forces" section="loads">
          <div className="spec-grid spec-grid-3">
            {Object.entries(spec.loads || {}).map(([key, value]) => (
              <div key={key} className="spec-item">
                <p className="spec-label">{key.replace('_', ' ')}</p>
                <p className="spec-value">
                  {value} {key.includes('kg') ? 'kg' : key.includes('torque') ? 'N·m' : 'N'}
                </p>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Materials" section="materials">
          <div className="spec-materials">
            {spec.materials && spec.materials.map((material, idx) => (
              <span key={idx} className="material-badge">
                {material}
              </span>
            ))}
          </div>
        </Section>

        <Section title="Components" section="components">
          {spec.components && spec.components.length > 0 ? (
            <div className="spec-components">
              {spec.components.map((component, idx) => (
                <div key={idx} className="component-card">
                  <div className="component-info">
                    <p className="component-name">{component.name || component.type}</p>
                    {component.mpn && (
                      <p className="component-mpn">MPN: {component.mpn}</p>
                    )}
                  </div>
                  <span className="component-qty">
                    Qty: {component.quantity}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="spec-empty">No components specified</p>
          )}
        </Section>
      </div>
    </div>
  );
}