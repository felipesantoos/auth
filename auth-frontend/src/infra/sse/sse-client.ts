/**
 * SSE (Server-Sent Events) Client
 * Wrapper for EventSource with auto-reconnection
 * Compliant with 25-real-time-streaming.md guide
 */

export interface SSEClientOptions {
  withCredentials?: boolean;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
}

export class SSEClient {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private reconnectDelay: number;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private eventHandlers: Map<string, Function[]> = new Map();
  private withCredentials: boolean;
  private isManualClose = false;
  
  constructor(
    private url: string,
    options: SSEClientOptions = {}
  ) {
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
    this.reconnectDelay = options.reconnectDelay || 1000;
    this.withCredentials = options.withCredentials || false;
  }
  
  connect(): void {
    this.isManualClose = false;
    
    try {
      // Create EventSource
      this.eventSource = new EventSource(this.url, {
        withCredentials: this.withCredentials
      });
      
      this.eventSource.onopen = () => {
        console.log('SSE connected');
        this.reconnectAttempts = 0;
        this.triggerEvent('connected', {});
      };
      
      this.eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        this.triggerEvent('error', { error });
        
        // Auto-reconnect on error (unless manually closed)
        if (!this.isManualClose) {
          this.eventSource?.close();
          this.reconnect();
        }
      };
      
      // Attach custom event listeners
      this.eventHandlers.forEach((handlers, eventType) => {
        handlers.forEach(handler => {
          this.eventSource?.addEventListener(eventType, (event: Event) => {
            const messageEvent = event as MessageEvent;
            try {
              const data = JSON.parse(messageEvent.data);
              handler(data, messageEvent);
            } catch (e) {
              // Data might not be JSON
              handler(messageEvent.data, messageEvent);
            }
          });
        });
      });
      
    } catch (error) {
      console.error('Failed to create EventSource:', error);
      this.reconnect();
    }
  }
  
  on(eventType: string, handler: Function): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType)!.push(handler);
    
    // If already connected, attach the listener
    if (this.eventSource) {
      this.eventSource.addEventListener(eventType, (event: Event) => {
        const messageEvent = event as MessageEvent;
        try {
          const data = JSON.parse(messageEvent.data);
          handler(data, messageEvent);
        } catch (e) {
          handler(messageEvent.data, messageEvent);
        }
      });
    }
  }
  
  off(eventType: string, handler?: Function): void {
    if (!handler) {
      this.eventHandlers.delete(eventType);
    } else {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index !== -1) {
          handlers.splice(index, 1);
        }
      }
    }
  }
  
  private triggerEvent(eventType: string, data: any): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in SSE handler for ${eventType}:`, error);
        }
      });
    }
  }
  
  private reconnect(): void {
    if (this.isManualClose) {
      return;
    }
    
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max SSE reconnection attempts reached');
      this.triggerEvent('max_reconnect_attempts', {
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
      `Reconnecting SSE in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );
    
    this.triggerEvent('reconnecting', {
      attempt: this.reconnectAttempts,
      delay
    });
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }
  
  close(): void {
    this.isManualClose = true;
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    
    this.triggerEvent('closed', {});
  }
  
  isConnected(): boolean {
    return this.eventSource?.readyState === EventSource.OPEN;
  }
  
  getReadyState(): number | null {
    return this.eventSource?.readyState || null;
  }
}

