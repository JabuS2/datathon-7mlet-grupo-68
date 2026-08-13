from exceptions import AppException


class BadRequest(AppException):
    def __init__(self, message="Bad request", code=None):
        super().__init__(message, 400, code)


class Unauthorized(AppException):
    def __init__(self, message="Unauthorized", code=None):
        super().__init__(message, 401, code)


class Forbidden(AppException):
    def __init__(self, message="Forbidden", code=None):
        super().__init__(message, 403, code)


class NotFound(AppException):
    def __init__(self, message="Not found", code=None):
        super().__init__(message, 404, code)


class Conflict(AppException):
    def __init__(self, message="Conflict", code=None):
        super().__init__(message, 409, code)


class TooManyRequests(AppException):
    def __init__(self, message="Too many requests", code=None):
        super().__init__(message, 429, code)


class InternalServerError(AppException):
    def __init__(self, message="Internal server error", code=None):
        super().__init__(message, 500, code)
