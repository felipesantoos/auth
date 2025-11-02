/**
 * HTTP Client Implementation
 * Axios-based implementation of IHttpClient with dual-mode authentication support
 * 
 * Security:
 * - Web mode: Uses httpOnly cookies (XSS protection)
 * - Sends X-Client-Type: web header
 * - withCredentials: true to send cookies
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { IHttpClient } from '../../core/interfaces/secondary/IHttpClient';

export class HttpClient implements IHttpClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        'X-Client-Type': 'web', // Indicate this is a web client (for dual-mode auth)
      },
      withCredentials: true, // Send cookies with requests (for httpOnly cookies)
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor - Add client_id to requests
    // NOTE: Access tokens are now sent via httpOnly cookies (no localStorage)
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Get client_id from localStorage and add to header
        // (client_id is not sensitive, so localStorage is OK)
        const clientId = localStorage.getItem('client_id');
        if (clientId) {
          config.headers['X-Client-ID'] = clientId;
        }

        // Access token is sent automatically via httpOnly cookie
        // No need to manually add Authorization header

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle token refresh with cookies
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error) => {
        const originalRequest = error.config;

        // If 401 and we haven't tried to refresh yet
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Try to refresh token (cookies sent automatically)
            // Backend reads refresh_token from cookie and sends new tokens via cookie
            const response = await axios.post(
              `${this.client.defaults.baseURL}/api/auth/refresh`,
              {}, // Empty body - refresh_token comes from cookie
              {
                withCredentials: true, // Send cookies
                headers: {
                  'X-Client-Type': 'web',
                },
              }
            );

            // New tokens are set in cookies by backend
            // No need to save anything to localStorage

            // Retry original request (new access_token cookie will be sent)
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, clear user data and redirect to login
            // Note: Cookies are httpOnly, they will be cleared by backend on logout
            localStorage.removeItem('user');
            localStorage.removeItem('client_id');
            
            // Redirect to login
            window.location.href = '/login';
            
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: any): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: any): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }
}

