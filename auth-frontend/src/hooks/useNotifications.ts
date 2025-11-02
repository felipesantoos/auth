/**
 * useNotifications Hook
 * React hook for real-time notifications via WebSocket
 * Compliant with 25-real-time-streaming.md guide
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  data?: any;
}

export interface UseNotificationsOptions {
  apiBaseUrl?: string;
  onNewNotification?: (notification: Notification) => void;
}

export interface UseNotificationsResult {
  notifications: Notification[];
  unreadCount: number;
  isConnected: boolean;
  markAsRead: (notificationId: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
  removeNotification: (notificationId: string) => void;
}

export function useNotifications(
  token: string,
  options: UseNotificationsOptions = {}
): UseNotificationsResult {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  
  const apiBaseUrl = options.apiBaseUrl || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
  const wsUrl = apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://');
  const notificationsWsUrl = `${wsUrl}/ws/notifications`;
  
  const { isConnected, on, off } = useWebSocket(notificationsWsUrl, token, {
    onConnected: () => {
      console.log('Notifications WebSocket connected');
    },
    onDisconnected: () => {
      console.log('Notifications WebSocket disconnected');
    }
  });
  
  // Handle incoming notifications
  useEffect(() => {
    const handleNotification = (data: any) => {
      if (data.notification) {
        const notification: Notification = {
          id: data.notification.id || String(Date.now()),
          type: data.notification.type || 'info',
          title: data.notification.title || 'Notification',
          message: data.notification.message || '',
          timestamp: data.notification.timestamp || new Date().toISOString(),
          read: false,
          data: data.notification.data
        };
        
        setNotifications(prev => [notification, ...prev]);
        options.onNewNotification?.(notification);
      }
    };
    
    on('notification', handleNotification);
    
    return () => {
      off('notification', handleNotification);
    };
  }, [on, off, options.onNewNotification]);
  
  const markAsRead = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.map(notif =>
        notif.id === notificationId
          ? { ...notif, read: true }
          : notif
      )
    );
  }, []);
  
  const markAllAsRead = useCallback(() => {
    setNotifications(prev =>
      prev.map(notif => ({ ...notif, read: true }))
    );
  }, []);
  
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);
  
  const removeNotification = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.filter(notif => notif.id !== notificationId)
    );
  }, []);
  
  const unreadCount = notifications.filter(n => !n.read).length;
  
  return {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    clearAll,
    removeNotification
  };
}

