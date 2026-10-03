import type { ApiErrorResponse, FieldError } from '../types/api';

/**
 * Normalized client error representing any API or network failure in Mobile.
 */
export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly errors?: FieldError[];
  public readonly isNetworkError: boolean;
  public readonly isTimeout: boolean;

  constructor(params: {
    message: string;
    status?: number;
    code?: string;
    errors?: FieldError[];
    isNetworkError?: boolean;
    isTimeout?: boolean;
  }) {
    super(params.message);
    this.name = 'ApiClientError';
    this.status = params.status ?? 0;
    this.code = params.code;
    this.errors = params.errors;
    this.isNetworkError = Boolean(params.isNetworkError);
    this.isTimeout = Boolean(params.isTimeout);
    Object.setPrototypeOf(this, ApiClientError.prototype);
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isValidationError(): boolean {
    return this.status === 422 || this.status === 400;
  }

  get isConflict(): boolean {
    return this.status === 409;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}

/**
 * Parses a fetch response or error into a normalized ApiClientError
 */
export async function parseApiError(response: Response): Promise<ApiClientError> {
  const status = response.status;
  let detail = `Request failed with status ${status}`;
  let code: string | undefined;
  let errors: FieldError[] | undefined;

  try {
    const data: ApiErrorResponse = await response.json();
    if (typeof data.detail === 'string') {
      detail = data.detail;
    } else if (Array.isArray(data.detail)) {
      detail = 'Validation error';
      errors = (data.detail as any[]).map((err: any) => ({
        field: Array.isArray(err.loc) ? err.loc.join('.') : undefined,
        message: err.msg || 'Invalid field',
      }));
    }
    code = data.code;
    if (data.errors) {
      errors = data.errors;
    }
  } catch {
    if (status === 404) detail = 'Resource not found';
    else if (status === 401) detail = 'Authentication required';
    else if (status === 403) detail = 'Access denied';
    else if (status >= 500) detail = 'Server error occurred. Please try again later.';
  }

  return new ApiClientError({
    message: detail,
    status,
    code,
    errors,
  });
}
