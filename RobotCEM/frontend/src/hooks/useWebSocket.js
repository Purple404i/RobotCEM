import { useEffect, useState } from 'react';

export function useWebSocket(url) {
  const [socket, setSocket] = useState(null);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);
    };

    setSocket(ws);

    return () => ws.close();
  }, [url]);

  return { socket, messages };
}
