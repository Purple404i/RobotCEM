import { useState, useEffect } from 'react';

export function useSTLLoader(url) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!url) return;
    
    setLoading(true);
    // STL loading logic here
    setLoading(false);
  }, [url]);

  return { loading, error };
}
