import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '../store/authStore';

interface WebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onAnalyticsUpdate?: (data: any) => void;
  onIntegrationStatus?: (data: any) => void;
  onAlert?: (data: any) => void;
}

export const useWebSocket = (options: WebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const user = useAuthStore(state => state.user);
  const accessToken = useAuthStore(state => state.accessToken);

  useEffect(() => {
    if (!user || !accessToken) return;

    // Prefer relative default so Vite dev proxy can handle WS in all envs
    const WS_URL = import.meta.env.VITE_WS_URL || '/socket.io';

    socketRef.current = io(WS_URL, {
      auth: {
        token: accessToken,
        userId: user.id,
        role: user.role,
        practiceIds: user.practiceIds
      },
      transports: ['websocket', 'polling'],
      timeout: 10000,
    });

    const socket = socketRef.current;

    // Connection handlers
    socket.on('connect', () => {
      setIsConnected(true);
      setError(null);
      options.onConnect?.();

      // Subscribe to role-based BI updates
      socket.emit('subscribe-analytics', {
        role: user.role,
        practiceIds: user.practiceIds
      });
    });

    socket.on('disconnect', (reason) => {
      setIsConnected(false);
      options.onDisconnect?.();

      if (reason === 'io server disconnect') {
        // Server disconnected, need to reconnect manually
        socket.connect();
      }
    });

    socket.on('connect_error', (error) => {
      setError(`Connection failed: ${error.message}`);
      setIsConnected(false);
    });

    // BI-specific event handlers
    socket.on('analytics-update', (data) => {
      options.onAnalyticsUpdate?.(data);
      try {
        window.dispatchEvent(new CustomEvent('analytics-update', { detail: data }));
      } catch {}
    });

    socket.on('integration-status-change', (data) => {
      options.onIntegrationStatus?.(data);
    });

    socket.on('bi-alert', (data) => {
      options.onAlert?.(data);
    });

    // Real-time KPI updates for executives
    socket.on('kpi-update', (data) => {
      if (user.role === 'executive' || user.role === 'admin') {
        options.onAnalyticsUpdate?.(data);
      }
    });

    // Manager operational updates
    socket.on('operational-update', (data) => {
      if (user.role === 'manager') {
        options.onAnalyticsUpdate?.(data);
      }
    });

    // Clinical metrics updates
    socket.on('clinical-update', (data) => {
      if (user.role === 'clinician') {
        options.onAnalyticsUpdate?.(data);
      }
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
      setIsConnected(false);
    };
  }, [user, accessToken]);

  // Methods to emit events
  const emitEvent = (eventName: string, data: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(eventName, data);
    }
  };

  const requestAnalyticsRefresh = () => {
    emitEvent('refresh-analytics', {
      role: user?.role,
      practiceIds: user?.practiceIds
    });
  };

  const requestIntegrationSync = (system: string) => {
    emitEvent('sync-integration', {
      system,
      practiceIds: user?.practiceIds
    });
  };

  return {
    isConnected,
    error,
    emitEvent,
    requestAnalyticsRefresh,
    requestIntegrationSync,
  };
};

// Specialized hook for BI dashboard real-time updates
export const useBIDashboardUpdates = () => {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [updateCount, setUpdateCount] = useState(0);

  const webSocket = useWebSocket({
    onConnect: () => {
      console.log('BI Dashboard connected to real-time updates');
    },
    onAnalyticsUpdate: (data) => {
      setLastUpdate(new Date());
      setUpdateCount(prev => prev + 1);

      // Trigger React Query cache invalidation for relevant data
      console.log('Analytics update received:', data);
    },
    onIntegrationStatus: (data) => {
      console.log('Integration status update:', data);
      setLastUpdate(new Date());
    },
    onAlert: (data) => {
      console.log('BI Alert received:', data);
      // This could trigger toast notifications for important alerts
    }
  });

  return {
    ...webSocket,
    lastUpdate,
    updateCount,
  };
};
