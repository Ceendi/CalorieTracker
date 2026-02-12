import { AxiosError, AxiosHeaders } from 'axios';
import {
  AppError,
  ErrorCode,
  getErrorMessage,
  isNetworkError,
  isAuthError,
  isValidationError,
  toAppError,
  getValidationErrors,
} from '../../../utils/errors';

function makeAxiosError(status: number, data: any = {}): AxiosError {
  const headers = new AxiosHeaders();
  return new AxiosError(
    `Request failed with status code ${status}`,
    String(status),
    { headers } as any,
    {},
    { data, status, statusText: `Error ${status}`, headers, config: { headers } as any }
  );
}

function makeNetworkError(): AxiosError {
  const err = new AxiosError('Network Error', 'ERR_NETWORK', undefined, {});
  (err as any).response = undefined;
  return err;
}

describe('AppError', () => {
  it('creates with message and code', () => {
    const err = new AppError('test', ErrorCode.UNKNOWN);
    expect(err.message).toBe('test');
    expect(err.code).toBe(ErrorCode.UNKNOWN);
    expect(err.name).toBe('AppError');
  });

  it('is instanceof Error', () => {
    expect(new AppError('x', ErrorCode.UNKNOWN)).toBeInstanceOf(Error);
  });

  it('stores original error', () => {
    const orig = new Error('orig');
    const err = new AppError('wrapped', ErrorCode.UNKNOWN, orig);
    expect(err.originalError).toBe(orig);
  });

  it('has undefined originalError when not provided', () => {
    const err = new AppError('x', ErrorCode.UNKNOWN);
    expect(err.originalError).toBeUndefined();
  });
});

describe('getErrorMessage', () => {
  it('returns AppError message', () => {
    expect(getErrorMessage(new AppError('custom msg', ErrorCode.UNKNOWN))).toBe('custom msg');
  });

  it('returns detail from AxiosError response', () => {
    expect(getErrorMessage(makeAxiosError(400, { detail: 'Bad input' }))).toBe('Bad input');
  });

  it('returns message from AxiosError response', () => {
    expect(getErrorMessage(makeAxiosError(400, { message: 'Server message' }))).toBe('Server message');
  });

  it('returns network error message when no response', () => {
    expect(getErrorMessage(makeNetworkError())).toBe('Błąd połączenia z serwerem. Sprawdź internet.');
  });

  it('returns status 400 message', () => {
    expect(getErrorMessage(makeAxiosError(400))).toBe('Nieprawidłowe dane żądania.');
  });

  it('returns status 401 message', () => {
    expect(getErrorMessage(makeAxiosError(401))).toBe('Sesja wygasła. Zaloguj się ponownie.');
  });

  it('returns status 403 message', () => {
    expect(getErrorMessage(makeAxiosError(403))).toBe('Brak dostępu do zasobu.');
  });

  it('returns status 404 message', () => {
    expect(getErrorMessage(makeAxiosError(404))).toBe('Nie znaleziono zasobu.');
  });

  it('returns status 409 message', () => {
    expect(getErrorMessage(makeAxiosError(409))).toBe('Konflikt danych. Spróbuj ponownie.');
  });

  it('returns status 422 message', () => {
    expect(getErrorMessage(makeAxiosError(422))).toBe('Nieprawidłowe dane. Sprawdź formularz.');
  });

  it('returns status 429 message', () => {
    expect(getErrorMessage(makeAxiosError(429))).toBe('Zbyt wiele żądań. Poczekaj chwilę.');
  });

  it('returns status 500 message', () => {
    expect(getErrorMessage(makeAxiosError(500))).toBe('Błąd serwera. Spróbuj później.');
  });

  it('returns generic status message for unknown status', () => {
    expect(getErrorMessage(makeAxiosError(503))).toBe('Błąd serwera (503).');
  });

  it('returns Error.message', () => {
    expect(getErrorMessage(new Error('plain error'))).toBe('plain error');
  });

  it('returns string error directly', () => {
    expect(getErrorMessage('some string')).toBe('some string');
  });

  it('returns generic for unknown types', () => {
    expect(getErrorMessage(42)).toBe('Wystąpił nieoczekiwany błąd.');
    expect(getErrorMessage(null)).toBe('Wystąpił nieoczekiwany błąd.');
  });
});

describe('isNetworkError', () => {
  it('returns true for AxiosError without response', () => {
    expect(isNetworkError(makeNetworkError())).toBe(true);
  });

  it('returns false for AxiosError with response', () => {
    expect(isNetworkError(makeAxiosError(500))).toBe(false);
  });

  it('returns false for non-Axios errors', () => {
    expect(isNetworkError(new Error('x'))).toBe(false);
  });
});

describe('isAuthError', () => {
  it('returns true for 401', () => {
    expect(isAuthError(makeAxiosError(401))).toBe(true);
  });

  it('returns true for 403', () => {
    expect(isAuthError(makeAxiosError(403))).toBe(true);
  });

  it('returns false for 404', () => {
    expect(isAuthError(makeAxiosError(404))).toBe(false);
  });

  it('returns true for AppError UNAUTHORIZED', () => {
    expect(isAuthError(new AppError('x', ErrorCode.UNAUTHORIZED))).toBe(true);
  });

  it('returns true for AppError FORBIDDEN', () => {
    expect(isAuthError(new AppError('x', ErrorCode.FORBIDDEN))).toBe(true);
  });

  it('returns true for AppError SESSION_EXPIRED', () => {
    expect(isAuthError(new AppError('x', ErrorCode.SESSION_EXPIRED))).toBe(true);
  });

  it('returns false for non-auth AppError', () => {
    expect(isAuthError(new AppError('x', ErrorCode.VALIDATION_ERROR))).toBe(false);
  });
});

describe('isValidationError', () => {
  it('returns true for 422 AxiosError', () => {
    expect(isValidationError(makeAxiosError(422))).toBe(true);
  });

  it('returns false for 400 AxiosError', () => {
    expect(isValidationError(makeAxiosError(400))).toBe(false);
  });

  it('returns true for AppError VALIDATION_ERROR', () => {
    expect(isValidationError(new AppError('x', ErrorCode.VALIDATION_ERROR))).toBe(true);
  });

  it('returns false for regular Error', () => {
    expect(isValidationError(new Error('x'))).toBe(false);
  });
});

describe('toAppError', () => {
  it('returns same AppError', () => {
    const err = new AppError('x', ErrorCode.UNKNOWN);
    expect(toAppError(err)).toBe(err);
  });

  it('converts network AxiosError', () => {
    const result = toAppError(makeNetworkError());
    expect(result.code).toBe(ErrorCode.NETWORK_ERROR);
  });

  it('converts 401 to UNAUTHORIZED', () => {
    expect(toAppError(makeAxiosError(401)).code).toBe(ErrorCode.UNAUTHORIZED);
  });

  it('converts 403 to FORBIDDEN', () => {
    expect(toAppError(makeAxiosError(403)).code).toBe(ErrorCode.FORBIDDEN);
  });

  it('converts 404 to NOT_FOUND', () => {
    expect(toAppError(makeAxiosError(404)).code).toBe(ErrorCode.NOT_FOUND);
  });

  it('converts 409 to CONFLICT', () => {
    expect(toAppError(makeAxiosError(409)).code).toBe(ErrorCode.CONFLICT);
  });

  it('converts 422 to VALIDATION_ERROR', () => {
    expect(toAppError(makeAxiosError(422)).code).toBe(ErrorCode.VALIDATION_ERROR);
  });

  it('converts 500 to SERVER_ERROR', () => {
    expect(toAppError(makeAxiosError(500)).code).toBe(ErrorCode.SERVER_ERROR);
  });

  it('converts 400 to UNKNOWN', () => {
    expect(toAppError(makeAxiosError(400)).code).toBe(ErrorCode.UNKNOWN);
  });

  it('converts plain Error', () => {
    const result = toAppError(new Error('plain'));
    expect(result.code).toBe(ErrorCode.UNKNOWN);
    expect(result.message).toBe('plain');
  });

  it('converts string', () => {
    const result = toAppError('string error');
    expect(result.message).toBe('string error');
  });

  it('converts null/unknown', () => {
    const result = toAppError(null);
    expect(result.message).toBe('Wystąpił nieoczekiwany błąd.');
  });
});

describe('getValidationErrors', () => {
  it('returns null for non-422', () => {
    expect(getValidationErrors(makeAxiosError(400))).toBeNull();
  });

  it('returns null for non-axios error', () => {
    expect(getValidationErrors(new Error('x'))).toBeNull();
  });

  it('parses FastAPI validation detail array', () => {
    const err = makeAxiosError(422, {
      detail: [
        { loc: ['body', 'email'], msg: 'Invalid email' },
        { loc: ['body', 'password'], msg: 'Too short' },
      ],
    });
    expect(getValidationErrors(err)).toEqual({ email: 'Invalid email', password: 'Too short' });
  });

  it('returns null for non-array detail', () => {
    expect(getValidationErrors(makeAxiosError(422, { detail: 'string' }))).toBeNull();
  });

  it('uses "unknown" when loc missing', () => {
    const err = makeAxiosError(422, { detail: [{ msg: 'Bad' }] });
    expect(getValidationErrors(err)).toEqual({ unknown: 'Bad' });
  });

  it('uses default message when msg missing', () => {
    const err = makeAxiosError(422, { detail: [{ loc: ['body', 'name'] }] });
    expect(getValidationErrors(err)).toEqual({ name: 'Nieprawidłowa wartość' });
  });
});
