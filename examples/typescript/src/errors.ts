/**
 * Error classes for Triggers API
 */

export class TriggersAPIError extends Error {
  statusCode: number | null;
  errorCode: string;
  details: Record<string, any>;
  requestId: string | null;

  constructor(
    message: string,
    statusCode: number | null = null,
    errorCode: string = 'UNKNOWN_ERROR',
    details: Record<string, any> = {},
    requestId: string | null = null
  ) {
    super(message);
    this.name = 'TriggersAPIError';
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
    this.requestId = requestId;
  }
}

export class ValidationError extends TriggersAPIError {
  constructor(
    message: string = 'Invalid request payload',
    statusCode: number = 400,
    errorCode: string = 'VALIDATION_ERROR',
    details: Record<string, any> = {},
    requestId: string | null = null
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'ValidationError';
  }
}

export class UnauthorizedError extends TriggersAPIError {
  constructor(
    message: string = 'Unauthorized',
    statusCode: number = 401,
    errorCode: string = 'UNAUTHORIZED',
    details: Record<string, any> = {},
    requestId: string | null = null
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'UnauthorizedError';
  }
}

export class NotFoundError extends TriggersAPIError {
  constructor(
    message: string = 'Resource not found',
    statusCode: number = 404,
    errorCode: string = 'NOT_FOUND',
    details: Record<string, any> = {},
    requestId: string | null = null
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'NotFoundError';
  }
}

export class ConflictError extends TriggersAPIError {
  constructor(
    message: string = 'Resource conflict',
    statusCode: number = 409,
    errorCode: string = 'CONFLICT',
    details: Record<string, any> = {},
    requestId: string | null = null
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'ConflictError';
  }
}

export class PayloadTooLargeError extends TriggersAPIError {
  constructor(
    message: string = 'Payload too large',
    statusCode: number = 413,
    errorCode: string = 'PAYLOAD_TOO_LARGE',
    details: Record<string, any> = {},
    requestId: string | null = null
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'PayloadTooLargeError';
  }
}

export class RateLimitExceededError extends TriggersAPIError {
  constructor(
    message: string = 'Rate limit exceeded',
    statusCode: number = 429,
    errorCode: string = 'RATE_LIMIT_EXCEEDED',
    details: Record<string, any> = {},
    requestId: string | null = null
  ) {
    super(message, statusCode, errorCode, details, requestId);
    this.name = 'RateLimitExceededError';
  }
}

export function mapStatusCodeToError(statusCode: number): typeof TriggersAPIError {
  switch (statusCode) {
    case 400:
      return ValidationError;
    case 401:
      return UnauthorizedError;
    case 404:
      return NotFoundError;
    case 409:
      return ConflictError;
    case 413:
      return PayloadTooLargeError;
    case 429:
      return RateLimitExceededError;
    default:
      return TriggersAPIError;
  }
}

