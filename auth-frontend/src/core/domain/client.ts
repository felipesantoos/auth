/**
 * Client Domain Models
 * TypeScript domain models for client (tenant)
 */

export interface Client {
  id: string;
  name: string;
  subdomain: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientResponse {
  id: string;
  name: string;
  subdomain: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateClientDTO {
  name: string;
  subdomain: string;
}

