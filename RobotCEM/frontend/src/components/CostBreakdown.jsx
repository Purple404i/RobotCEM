import React from 'react';

export default function CostBreakdown({ bom }) {
  if (!bom) return null;

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-xl font-bold mb-4">Cost Breakdown</h3>
      <div className="space-y-2">
        <div className="flex justify-between">
          <span>Materials:</span>
          <span>${bom.summary.subtotal_usd}</span>
        </div>
        <div className="flex justify-between">
          <span>Shipping:</span>
          <span>${bom.summary.shipping_usd}</span>
        </div>
        <div className="flex justify-between font-bold text-lg border-t border-gray-700 pt-2 mt-2">
          <span>Total:</span>
          <span className="text-green-400">${bom.summary.total_usd}</span>
        </div>
      </div>
    </div>
  );
}
