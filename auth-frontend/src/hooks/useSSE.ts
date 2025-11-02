/**
 * useSSE Hook
 * React hook for consuming Server-Sent Events
 * Compliant with 25-real-time-streaming.md guide
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { SSEClient, SSEClientOptions } from '../infra/sse/sse-client';

export interface UseSSEOptions extends SSEClientOptions {
  onConnected?: () => void;
  onError?: (error: any) => void;
  onReconnecting?: (attempt: number, delay: number) => void;
  autoConnect?: boolean;
}

export interface UseSSEResult<T> {
  data: T | null;
  error: any | null;
  isConnected: boolean;
  reconnect: () => void;
  close: () => void;
}

export function useSSE<T = any>(
  url: string,
  eventType: string = 'message',
  options: UseSSEOptions = {}
): UseSSEResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<any | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const clientRef = useRef<SSEClient | null>(null);
  
  const {
    onConnected,
    onError,
    onReconnecting,
    autoConnect = true,
    ...clientOptions
  } = options;
  
  const handleConnected = useCallback(() => {
    setIsConnected(true);
    setError(null);
    onConnected?.();
  }, [onConnected]);
  
  const handleError = useCallback((errorData: any) => {
    setError(errorData.error);
    setIsConnected(false);
    onError?.(errorData.error);
  }, [onError]);
  
  const handleReconnecting = useCallback((reconnectData: any) => {
    setIsConnected(false);
    onReconnecting?.(reconnectData.attempt, reconnectData.delay);
  }, [onReconnecting]);
  
  const handleMessage = useCallback((messageData: any) => {
    setData(messageData);
  }, []);
  
  useEffect(() => {
    if (!url) {
      return;
    }
    
    // Create SSE client
    const client = new SSEClient(url, clientOptions);
    clientRef.current = client;
    
    // Register event handlers
    client.on('connected', handleConnected);
    client.on('error', handleError);
    client.on('reconnecting', handleReconnecting);
    client.on(eventType, handleMessage);
    
    // Connect if autoConnect is true
    if (autoConnect) {
      client.connect();
    }
    
    // Cleanup on unmount
    return () => {
      client.close();
      clientRef.current = null;
    };
  }, [url, eventType, autoConnect, handleConnected, handleError, handleReconnecting, handleMessage]);
  
  const reconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.close();
      clientRef.current.connect();
    }
  }, []);
  
  const close = useCallback(() => {
    clientRef.current?.close();
  }, []);
  
  return {
    data,
    error,
    isConnected,
    reconnect,
    close
  };
}

