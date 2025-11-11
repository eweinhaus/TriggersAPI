/**
 * Error classes for Triggers API client
 */

class TriggersAPIError extends Error {
    constructor(message, statusCode = null, errorCode = null, details = {}, requestId = null) {
        super(message);
        this.name = 'TriggersAPIError';
        this.message = message;
        this.statusCode = statusCode;
        this.errorCode = errorCode;
        this.details = details;
        this.requestId = requestId;
    }

    toString() {
        const parts = [this.message];
        if (this.errorCode) parts.push(`Code: ${this.errorCode}`);
        if (this.statusCode) parts.push(`Status: ${this.statusCode}`);
        if (this.requestId) parts.push(`Request ID: ${this.requestId}`);
        return parts.join(' | ');
    }
}

class ValidationError extends TriggersAPIError {
    constructor(message, statusCode, errorCode, details, requestId) {
        super(message, statusCode, errorCode, details, requestId);
        this.name = 'ValidationError';
    }
}

class UnauthorizedError extends TriggersAPIError {
    constructor(message, statusCode, errorCode, details, requestId) {
        super(message, statusCode, errorCode, details, requestId);
        this.name = 'UnauthorizedError';
    }
}

class NotFoundError extends TriggersAPIError {
    constructor(message, statusCode, errorCode, details, requestId) {
        super(message, statusCode, errorCode, details, requestId);
        this.name = 'NotFoundError';
    }
}

class ConflictError extends TriggersAPIError {
    constructor(message, statusCode, errorCode, details, requestId) {
        super(message, statusCode, errorCode, details, requestId);
        this.name = 'ConflictError';
    }
}

class PayloadTooLargeError extends TriggersAPIError {
    constructor(message, statusCode, errorCode, details, requestId) {
        super(message, statusCode, errorCode, details, requestId);
        this.name = 'PayloadTooLargeError';
    }
}

class RateLimitError extends TriggersAPIError {
    constructor(message, statusCode, errorCode, details, requestId) {
        super(message, statusCode, errorCode, details, requestId);
        this.name = 'RateLimitError';
    }
}

class InternalError extends TriggersAPIError {
    constructor(message, statusCode, errorCode, details, requestId) {
        super(message, statusCode, errorCode, details, requestId);
        this.name = 'InternalError';
    }
}

function mapStatusCodeToError(statusCode) {
    const mapping = {
        400: ValidationError,
        401: UnauthorizedError,
        404: NotFoundError,
        409: ConflictError,
        413: PayloadTooLargeError,
        429: RateLimitError,
        500: InternalError,
    };
    return mapping[statusCode] || TriggersAPIError;
}

module.exports = {
    TriggersAPIError,
    ValidationError,
    UnauthorizedError,
    NotFoundError,
    ConflictError,
    PayloadTooLargeError,
    RateLimitError,
    InternalError,
    mapStatusCodeToError,
};

