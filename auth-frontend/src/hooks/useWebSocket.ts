/**
 * useWebSocket Hook
 * React hook for managing WebSocket connections
 * Compliant with 25-real-time-streaming.md guide
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketClientOptions } from '../infra/websocket/websocket-client';
import { WebSocketClient } from '../infra/websocket/websocket-client';

export interface UseWebSocketOptions extends WebSocketClientOptions {
  onConnected?: () => void;
  onDisconnected?: (code?: number, reason?: string) => void;
  onError?: (error: any) => void;
  onReconnecting?: (attempt: number, delay: number) => void;
}

export interface UseWebSocketResult {
  isConnected: boolean;
  send: (message: unknown) => void;
  on: (messageType: string, handler: (...args: unknown[]) => void) => void;
  off: (messageType: string, handler?: (...args: unknown[]) => void) => void;
  reconnect: () => void;
  disconnect: () => void;
  readyState: number | null;
}

export function useWebSocket(
  url: string,
  token: string,
  options: UseWebSocketOptions = {}
): UseWebSocketResult {
  const [isConnected, setIsConnected] = useState(false);
  const [readyState, setReadyState] = useState<number | null>(null);
  const clientRef = useRef<WebSocketClient | null>(null);
  
  // Stable callbacks
  const {
    onConnected,
    onDisconnected,
    onError,
    onReconnecting,
    ...clientOptions
  } = options;
  
  const handleConnected = useCallback(() => {
    setIsConnected(true);
    setReadyState(WebSocket.OPEN);
    onConnected?.();
  }, [onConnected]);
  
  const handleDisconnected = useCallback((data: any) => {
    setIsConnected(false);
    setReadyState(WebSocket.CLOSED);
    onDisconnected?.(data.code, data.reason);
  }, [onDisconnected]);
  
  const handleError = useCallback((data: any) => {
    onError?.(data.error);
  }, [onError]);
  
  const handleReconnecting = useCallback((data: any) => {
    setReadyState(WebSocket.CONNECTING);
    onReconnecting?.(data.attempt, data.delay);
  }, [onReconnecting]);
  
  useEffect(() => {
    if (!url || !token) {
      return;
    }
    
    // Create WebSocket client
    const client = new WebSocketClient(url, token, clientOptions);
    clientRef.current = client;
    
    // Register event handlers
    client.on('connected', handleConnected);
    client.on('disconnected', handleDisconnected);
    client.on('error', handleError);
    client.on('reconnecting', handleReconnecting);
    
    // Update ready state periodically
    const interval = setInterval(() => {
      setReadyState(client.getReadyState());
    }, 1000);
    
    // Cleanup on unmount
    return () => {
      clearInterval(interval);
      client.disconnect();
      clientRef.current = null;
    };
  }, [url, token, handleConnected, handleDisconnected, handleError, handleReconnecting]);
  
  const send = useCallback((message: any) => {
    clientRef.current?.send(message);
  }, []);
  
  const on = useCallback((messageType: string, handler: (...args: unknown[]) => void) => {
    clientRef.current?.on(messageType, handler);
  }, []);
  
  const off = useCallback((messageType: string, handler?: (...args: unknown[]) => void) => {
    clientRef.current?.off(messageType, handler);
  }, []);
  
  const reconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current.connect();
    }
  }, []);
  
  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);
  
  return {
    isConnected,
    send,
    on,
    off,
    reconnect,
    disconnect,
    readyState
  };
}

