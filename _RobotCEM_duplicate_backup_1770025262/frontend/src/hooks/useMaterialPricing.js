import { useState, useEffect } from 'react';

export function useMaterialPricing(material) {
  const [price, setPrice] = useState(null);

  useEffect(() => {
    // Fetch material pricing
    setPrice(20.0); // Default
  }, [material]);

  return price;
}
