import React, { useState } from 'react';
import './BOMTable.css';
import { Download, ExternalLink, Package, DollarSign, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

export default function BOMTable({ bom }) {
  const [sortBy, setSortBy] = useState('category');
  const [sortOrder, setSortOrder] = useState('asc');
  const [filterCategory, setFilterCategory] = useState('all');

  if (!bom || !bom.items) {
    return (
      <div className="bom-empty">
        <Package size={48} className="bom-empty-icon" />
        <p className="bom-empty-text">No Bill of Materials generated yet</p>
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
      '3D Printed Parts': 'category-blue',
      'Electronic Components': 'category-purple',
      'Hardware': 'category-green',
      'Mechanical': 'category-orange'
    };
    return colors[category] || 'category-gray';
  };

  const getStockStatus = (item) => {
    if (!item.stock || item.stock === 'Unknown') return null;
    
    const stock = parseInt(item.stock);
    const needed = item.quantity;
    
    if (stock >= needed * 10) {
      return { icon: CheckCircle, color: 'stock-good', text: 'In Stock' };
    } else if (stock >= needed) {
      return { icon: AlertTriangle, color: 'stock-low', text: 'Low Stock' };
    } else {
      return { icon: AlertTriangle, color: 'stock-out', text: 'Insufficient' };
    }
  };

  return (
    <div className="bom-container">
      {/* Header */}
      <div className="bom-header">
        <div className="bom-header-content">
          <div className="bom-title-section">
            <Package size={28} />
            <div>
              <h2 className="bom-title">Bill of Materials</h2>
              <p className="bom-subtitle">Complete component breakdown with real-time pricing</p>
            </div>
          </div>
          <div className="bom-export-buttons">
            <button onClick={exportCSV} className="export-btn">
              <Download size={18} />
              CSV
            </button>
            <button onClick={exportJSON} className="export-btn">
              <Download size={18} />
              JSON
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="bom-summary">
        <div className="summary-card">
          <div className="summary-label">
            <Package size={16} />
            Total Items
          </div>
          <div className="summary-value">{bom.summary.item_count}</div>
          <div className="summary-hint">Unique components</div>
        </div>
        
        <div className="summary-card">
          <div className="summary-label">
            <DollarSign size={16} />
            Subtotal
          </div>
          <div className="summary-value">${bom.summary.subtotal_usd.toFixed(2)}</div>
          <div className="summary-hint">Before tax & shipping</div>
        </div>
        
        <div className="summary-card">
          <div className="summary-label">
            <TrendingUp size={16} />
            Total Cost
          </div>
          <div className="summary-value summary-value-accent">${bom.summary.total_usd.toFixed(2)}</div>
          <div className="summary-hint">Incl. tax & shipping</div>
        </div>
        
        <div className="summary-card">
          <div className="summary-label">
            Weight
          </div>
          <div className="summary-value">{bom.summary.total_weight_g.toFixed(0)}g</div>
          <div className="summary-hint">Total assembly weight</div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="bom-filter">
        <span className="filter-label">Filter:</span>
        <div className="filter-buttons">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`filter-btn ${filterCategory === cat ? 'filter-btn-active' : ''}`}
            >
              {cat === 'all' ? 'All' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bom-table-wrapper">
        <table className="bom-table">
          <thead className="bom-table-head">
            <tr>
              <th className="bom-th">Category</th>
              <th className="bom-th bom-th-sortable" onClick={() => toggleSort('item')}>
                <div className="bom-th-content">
                  Item
                  {sortBy === 'item' && <span className="sort-arrow">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                </div>
              </th>
              <th className="bom-th">MPN</th>
              <th className="bom-th bom-th-sortable" onClick={() => toggleSort('quantity')}>
                <div className="bom-th-content">
                  Qty
                  {sortBy === 'quantity' && <span className="sort-arrow">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                </div>
              </th>
              <th className="bom-th bom-th-sortable" onClick={() => toggleSort('unit_cost_usd')}>
                <div className="bom-th-content">
                  Unit Cost
                  {sortBy === 'unit_cost_usd' && <span className="sort-arrow">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                </div>
              </th>
              <th className="bom-th bom-th-sortable" onClick={() => toggleSort('total_cost_usd')}>
                <div className="bom-th-content">
                  Total
                  {sortBy === 'total_cost_usd' && <span className="sort-arrow">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                </div>
              </th>
              <th className="bom-th">Supplier</th>
              <th className="bom-th">Stock</th>
              <th className="bom-th"></th>
            </tr>
          </thead>
          <tbody className="bom-table-body">
            {sortedItems.map((item, idx) => {
              const stockStatus = getStockStatus(item);
              
              return (
                <tr key={idx} className="bom-tr">
                  <td className="bom-td">
                    <span className={`category-badge ${getCategoryColor(item.category)}`}>
                      {item.category}
                    </span>
                  </td>
                  <td className="bom-td bom-td-item">{item.item}</td>
                  <td className="bom-td bom-td-mono">{item.mpn || 'N/A'}</td>
                  <td className="bom-td bom-td-center">{item.quantity}</td>
                  <td className="bom-td bom-td-mono">${item.unit_cost_usd.toFixed(2)}</td>
                  <td className="bom-td bom-td-mono bom-td-bold">${item.total_cost_usd.toFixed(2)}</td>
                  <td className="bom-td">{item.supplier}</td>
                  <td className="bom-td">
                    {stockStatus && (
                      <div className="stock-status">
                        <stockStatus.icon size={16} className={stockStatus.color} />
                        <span className={`stock-text ${stockStatus.color}`}>{stockStatus.text}</span>
                      </div>
                    )}
                  </td>
                  <td className="bom-td">
                    {item.mpn && (
                      <a
                        href={`https://octopart.com/search?q=${item.mpn}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="external-link"
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
      <div className="bom-footer">
        <div className="cost-breakdown">
          <div className="cost-row">
            <span className="cost-label">Subtotal:</span>
            <span className="cost-value">${bom.summary.subtotal_usd.toFixed(2)}</span>
          </div>
          <div className="cost-row">
            <span className="cost-label">Shipping (est.):</span>
            <span className="cost-value">${bom.summary.shipping_usd.toFixed(2)}</span>
          </div>
          <div className="cost-row">
            <span className="cost-label">Tax (est.):</span>
            <span className="cost-value">${bom.summary.tax_usd.toFixed(2)}</span>
          </div>
          <div className="cost-row cost-row-total">
            <span className="cost-label-total">Total:</span>
            <span className="cost-value-total">${bom.summary.total_usd.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}