export function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
}

export function formatNumber(num) {
  return new Intl.NumberFormat('en-US').format(num);
}
