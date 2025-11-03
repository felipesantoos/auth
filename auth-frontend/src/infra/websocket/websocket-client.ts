/**
 * WebSocket Client
 * Full-featured WebSocket client with auto-reconnection and exponential backoff
 * Compliant with 25-real-time-streaming.md guide
 */

export interface WebSocketClientOptions {
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  autoConnect?: boolean;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private url: string;
  private token: string;
  private reconnectDelay: number;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private heartbeatIntervalTime: number;
  private messageHandlers: Map<string, ((...args: unknown[]) => void)[]> = new Map();
  private reconnectTimeout: NodeJS.Timeout | null = null;
  
  constructor(
    url: string,
    token: string,
    options: WebSocketClientOptions = {}
  ) {
    this.url = url;
    this.token = token;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
    this.reconnectDelay = options.reconnectDelay || 1000;
    this.heartbeatIntervalTime = options.heartbeatInterval || 30000;
    
    if (options.autoConnect !== false) {
      this.connect();
    }
  }
  
  connect(): void {
    const wsUrl = `${this.url}?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.startHeartbeat();
      
      // Trigger connected event
      this.handleMessage({ type: 'connected' });
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.stopHeartbeat();
      
      // Trigger disconnected event
      this.handleMessage({ type: 'disconnected', code: event.code, reason: event.reason });
      
      // Auto-reconnect unless intentionally closed
      if (event.code !== 1000) {
        this.reconnect();
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      
      // Trigger error event
      this.handleMessage({ type: 'error', error });
    };
  }
  
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }
  
  on(messageType: string, handler: (...args: unknown[]) => void): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }
  
  off(messageType: string, handler?: (...args: unknown[]) => void): void {
    if (!handler) {
      this.messageHandlers.delete(messageType);
    } else {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index !== -1) {
          handlers.splice(index, 1);
        }
      }
    }
  }
  
  private handleMessage(data: any): void {
    const handlers = this.messageHandlers.get(data.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in handler for message type ${data.type}:`, error);
        }
      });
    }
    
    // Handle heartbeat/pong
    if (data.type === 'heartbeat' || data.type === 'pong') {
      // Connection is alive
      return;
    }
  }
  
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping', timestamp: Date.now() });
    }, this.heartbeatIntervalTime);
  }
  
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.handleMessage({ 
        type: 'max_reconnect_attempts',
        attempts: this.reconnectAttempts
      });
      return;
    }
    
    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      30000
    );
    
    console.log(
      `Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );
    
    this.handleMessage({
      type: 'reconnecting',
      attempt: this.reconnectAttempts,
      delay
    });
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }
  
  disconnect(): void {
    this.stopHeartbeat();
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }
  
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
  
  getReadyState(): number | null {
    return this.ws?.readyState || null;
  }
}

