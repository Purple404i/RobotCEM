import React from 'react';
import { Download } from 'lucide-react';

export default function ExportOptions({ jobId }) {
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-xl font-bold mb-4">Export Options</h3>
      <div className="space-y-2">
        <button className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded">
          <Download size={18} />
          Download STL
        </button>
        <button className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded">
          <Download size={18} />
          Download BOM (CSV)
        </button>
      </div>
    </div>
  );
}
