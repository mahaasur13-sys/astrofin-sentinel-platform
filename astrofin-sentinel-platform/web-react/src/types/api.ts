export interface ApiResponse<T> {
  data: T;
  meta?: {
    total: number;
    page: number;
    pageSize: number;
  };
}

export interface ApiErrorResponse {
  code: string;
  message: string;
  trace_id: string;
  correlation_id: string;
  status: number;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}
