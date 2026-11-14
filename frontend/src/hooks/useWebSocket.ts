import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketEvent {
  event: string;
  server_id: string;
  server_name: string;
  timestamp: string;
  cpu_percent: number;
  ram_percent: number;
  disk_percent: number;
  net_upload_speed: number;
  net_download_speed: number;
  new_alerts_count: number;
  is_anomaly: boolean;
}

export function useWebSocket(onMetricUpdate?: (data: WebSocketEvent) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const connect = useCallback(() => {
    const token = localStorage.getItem('cp_token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use window.location.host or direct port 8000 in dev
    const host = window.location.port === '5173' ? '127.0.0.1:8000' : window.location.host;
    const url = `${protocol}//${host}/ws?token=${token || ''}`;

    try {
      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('[CloudPulse WS] Connected to real-time telemetry stream.');
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === 'METRIC_UPDATE' && onMetricUpdate) {
            onMetricUpdate(payload);
          }
        } catch (e) {
          // non-json or ping/pong
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('[CloudPulse WS] Disconnected. Reconnecting in 3s...');
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.warn('[CloudPulse WS] Error:', err);
        ws.close();
      };
    } catch (e) {
      console.error('[CloudPulse WS] Connection initialization failed:', e);
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, [onMetricUpdate]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (socketRef.current) socketRef.current.close();
    };
  }, [connect]);

  return { isConnected };
}
