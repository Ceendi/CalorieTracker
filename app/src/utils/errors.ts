import axios from 'axios';

/**
 * Custom application error with error code and original error context
 */
export class AppError extends Error {
  constructor(
    message: string,
    public code: ErrorCode,
    public originalError?: unknown
  ) {
    super(message);
    this.name = 'AppError';
  }
}

/**
 * Error codes for categorizing errors
 */
export enum ErrorCode {
  // Network errors
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT = 'TIMEOUT',

  // Auth errors
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  SESSION_EXPIRED = 'SESSION_EXPIRED',
  INVALID_CREDENTIALS = 'INVALID_CREDENTIALS',
  AUTH_GOOGLE_PLAY_SERVICES = 'AUTH_GOOGLE_PLAY_SERVICES',

  // Validation errors
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INVALID_INPUT = 'INVALID_INPUT',

  // Server errors
  SERVER_ERROR = 'SERVER_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  CONFLICT = 'CONFLICT',

  // Client errors
  UNKNOWN = 'UNKNOWN',
}

/**
 * Extract user-friendly error message from any error type
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AppError) {
    return error.message;
  }

  if (axios.isAxiosError(error)) {
    // Server responded with error
    if (error.response?.data?.detail) {
      return String(error.response.data.detail);
    }
    if (error.response?.data?.message) {
      return String(error.response.data.message);
    }

    // Network error (no response)
    if (!error.response) {
      return 'Błąd połączenia z serwerem. Sprawdź internet.';
    }

    // HTTP status based messages
    switch (error.response.status) {
      case 400: return 'Nieprawidłowe dane żądania.';
      case 401: return 'Sesja wygasła. Zaloguj się ponownie.';
      case 403: return 'Brak dostępu do zasobu.';
      case 404: return 'Nie znaleziono zasobu.';
      case 409: return 'Konflikt danych. Spróbuj ponownie.';
      case 422: return 'Nieprawidłowe dane. Sprawdź formularz.';
      case 429: return 'Zbyt wiele żądań. Poczekaj chwilę.';
      case 500: return 'Błąd serwera. Spróbuj później.';
      default: return `Błąd serwera (${error.response.status}).`;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  return 'Wystąpił nieoczekiwany błąd.';
}

/**
 * Check if error is a network error (no response from server)
 */
export function isNetworkError(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response;
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    return error.response?.status === 401 || error.response?.status === 403;
  }
  if (error instanceof AppError) {
    return [ErrorCode.UNAUTHORIZED, ErrorCode.FORBIDDEN, ErrorCode.SESSION_EXPIRED].includes(error.code);
  }
  return false;
}

/**
 * Check if error is a validation error (422)
 */
export function isValidationError(error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    return error.response?.status === 422;
  }
  if (error instanceof AppError) {
    return error.code === ErrorCode.VALIDATION_ERROR;
  }
  return false;
}

/**
 * Convert any error to AppError with appropriate code
 */
export function toAppError(error: unknown): AppError {
  if (error instanceof AppError) {
    return error;
  }

  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return new AppError(
        'Błąd połączenia z serwerem.',
        ErrorCode.NETWORK_ERROR,
        error
      );
    }

    const status = error.response.status;
    const message = getErrorMessage(error);

    let code: ErrorCode;
    switch (status) {
      case 401: code = ErrorCode.UNAUTHORIZED; break;
      case 403: code = ErrorCode.FORBIDDEN; break;
      case 404: code = ErrorCode.NOT_FOUND; break;
      case 409: code = ErrorCode.CONFLICT; break;
      case 422: code = ErrorCode.VALIDATION_ERROR; break;
      default: code = status >= 500 ? ErrorCode.SERVER_ERROR : ErrorCode.UNKNOWN;
    }

    return new AppError(message, code, error);
  }

  if (error instanceof Error) {
    return new AppError(error.message, ErrorCode.UNKNOWN, error);
  }

  return new AppError(
    typeof error === 'string' ? error : 'Wystąpił nieoczekiwany błąd.',
    ErrorCode.UNKNOWN,
    error
  );
}

/**
 * Extract validation errors from 422 response
 */
export function getValidationErrors(error: unknown): Record<string, string> | null {
  if (!axios.isAxiosError(error) || error.response?.status !== 422) {
    return null;
  }

  const detail = error.response.data?.detail;

  // FastAPI validation error format
  if (Array.isArray(detail)) {
    const errors: Record<string, string> = {};
    for (const item of detail) {
      const field = item.loc?.[item.loc.length - 1] || 'unknown';
      errors[field] = item.msg || 'Nieprawidłowa wartość';
    }
    return errors;
  }

  return null;
}
