import React, { useState } from 'react';
import { Download, ExternalLink, Package, DollarSign, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

export default function BOMTable({ bom }) {
  const [sortBy, setSortBy] = useState('category');
  const [sortOrder, setSortOrder] = useState('asc');
  const [filterCategory, setFilterCategory] = useState('all');

  if (!bom || !bom.items) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
        <Package size={48} className="mx-auto mb-4 text-gray-600" />
        <p className="text-gray-400">No Bill of Materials generated yet</p>
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
      return sortOrder === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }
    
    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const exportCSV = () => {
    const headers = ['Category', 'Item', 'MPN', 'Quantity', 'Unit Cost ($)', 'Total Cost ($)', 'Supplier', 'Stock', 'Specifications'];
    const rows = bom.items.map(item => [
      item.category,
      item.item,
      item.mpn || 'N/A',
      item.quantity,
      item.unit_cost_usd.toFixed(2),
      item.total_cost_usd.toFixed(2),
      item.supplier,
      item.stock || 'N/A',
      JSON.stringify(item.specifications || {})
    ]);

    const csv = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bom_${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const exportJSON = () => {
    const json = JSON.stringify(bom, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bom_${Date.now()}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getCategoryColor = (category) => {
    const colors = {
      '3D Printed Parts': 'bg-blue-500',
      'Electronic Components': 'bg-purple-500',
      'Hardware': 'bg-green-500',
      'Mechanical': 'bg-orange-500'
    };
    return colors[category] || 'bg-gray-500';
  };

  const getStockStatus = (item) => {
    if (!item.stock || item.stock === 'Unknown') return null;
    
    const stock = parseInt(item.stock);
    const needed = item.quantity;
    
    if (stock >= needed * 10) {
      return { icon: CheckCircle, color: 'text-green-500', text: 'In Stock' };
    } else if (stock >= needed) {
      return { icon: AlertTriangle, color: 'text-yellow-500', text: 'Low Stock' };
    } else {
      return { icon: AlertTriangle, color: 'text-red-500', text: 'Insufficient' };
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Package size={28} />
            <div>
              <h2 className="text-2xl font-bold">Bill of Materials</h2>
              <p className="text-sm text-blue-100">Complete component breakdown with real-time pricing</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={exportCSV}
              className="flex items-center gap-2 px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded transition-colors"
            >
              <Download size={18} />
              CSV
            </button>
            <button
              onClick={exportJSON}
              className="flex items-center gap-2 px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded transition-colors"
            >
              <Download size={18} />
              JSON
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 bg-gray-900">
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
            <Package size={16} />
            Total Items
          </div>
          <div className="text-3xl font-bold">{bom.summary.item_count}</div>
          <div className="text-xs text-gray-500 mt-1">Unique components</div>
        </div>
        
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
            <DollarSign size={16} />
            Subtotal
          </div>
          <div className="text-3xl font-bold">${bom.summary.subtotal_usd.toFixed(2)}</div>
          <div className="text-xs text-gray-500 mt-1">Before tax & shipping</div>
        </div>
        
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
            <TrendingUp size={16} />
            Total Cost
          </div>
          <div className="text-3xl font-bold text-green-400">${bom.summary.total_usd.toFixed(2)}</div>
          <div className="text-xs text-gray-500 mt-1">Incl. tax & shipping</div>
        </div>
        
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
            Weight
          </div>
          <div className="text-3xl font-bold">{bom.summary.total_weight_g.toFixed(0)}g</div>
          <div className="text-xs text-gray-500 mt-1">Total assembly weight</div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="px-6 py-3 bg-gray-900 border-t border-b border-gray-700">
        <div className="flex items-center gap-2 overflow-x-auto">
          <span className="text-sm text-gray-400 whitespace-nowrap">Filter:</span>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1 rounded text-sm whitespace-nowrap transition-colors ${
                filterCategory === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {cat === 'all' ? 'All' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-900 border-b border-gray-700 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">
                Category
              </th>
              {['Item', 'MPN', 'Qty', 'Unit Cost', 'Total', 'Supplier', 'Stock'].map(field => (
                <th
                  key={field}
                  onClick={() => toggleSort(field.toLowerCase().replace(' ', '_') + '_usd')}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider cursor-pointer hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {field}
                    {sortBy.includes(field.toLowerCase()) && (
                      <span className="text-blue-400">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
              ))}
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {sortedItems.map((item, idx) => {
              const stockStatus = getStockStatus(item);
              
              return (
                <tr key={idx} className="hover:bg-gray-750 transition-colors">
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium text-white ${getCategoryColor(item.category)}`}>
                      {item.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium">{item.item}</td>
                  <td className="px-4 py-3 text-sm text-gray-400 font-mono">{item.mpn || 'N/A'}</td>
                  <td className="px-4 py-3 text-center">{item.quantity}</td>
                  <td className="px-4 py-3 font-mono">${item.unit_cost_usd.toFixed(2)}</td>
                  <td className="px-4 py-3 font-mono font-semibold">${item.total_cost_usd.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm">{item.supplier}</td>
                  <td className="px-4 py-3">
                    {stockStatus && (
                      <div className="flex items-center gap-2">
                        <stockStatus.icon size={16} className={stockStatus.color} />
                        <span className={`text-sm ${stockStatus.color}`}>{stockStatus.text}</span>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {item.mpn && (
                      <a
                        href={`https://octopart.com/search?q=${item.mpn}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        <ExternalLink size={16} />
                      </a>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Cost Breakdown */}
      <div className="p-6 bg-gray-900 border-t border-gray-700">
        <div className="max-w-md ml-auto space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Subtotal:</span>
            <span className="font-mono">${bom.summary.subtotal_usd.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Shipping (est.):</span>
            <span className="font-mono">${bom.summary.shipping_usd.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Tax (est.):</span>
            <span className="font-mono">${bom.summary.tax_usd.toFixed(2)}</span>
          </div>
          <div className="border-t border-gray-700 pt-2 mt-2">
            <div className="flex justify-between text-lg font-bold">
              <span>Total:</span>
              <span className="text-green-400">${bom.summary.total_usd.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}