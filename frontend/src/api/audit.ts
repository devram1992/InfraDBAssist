
import { apiClient } from "./client";

export type AuditStatus =
  | "success"
  | "denied"
  | "validation_failed"
  | "error";

export interface AuditEvent {
  user_id: string;
  username: string;
  roles: string[];
  tool_name: string;
  permission: string;
  request: Record<string, unknown>;
  status: AuditStatus;
  timestamp: string;
}

export interface AuditEventsResponse {
  items: AuditEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditFilters {
  user_id?: string;
  tool_name?: string;
  status?: AuditStatus;
  start_time?: string;
  end_time?: string;
  limit?: number;
  offset?: number;
}

export async function getAuditEvents(
  filters: AuditFilters = {},
): Promise<AuditEventsResponse> {
  const response = await apiClient.get<AuditEventsResponse>("/audit", {
    params: filters,
  });

  return response.data;
}

