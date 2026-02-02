import React from 'react';

export default function MaterialSelector({ selected, onChange }) {
  const materials = ['PLA', 'ABS', 'PETG', 'Nylon'];

  return (
    <select 
      value={selected} 
      onChange={(e) => onChange(e.target.value)}
      className="px-4 py-2 bg-gray-800 border border-gray-700 rounded"
    >
      {materials.map(m => (
        <option key={m} value={m}>{m}</option>
      ))}
    </select>
  );
}
