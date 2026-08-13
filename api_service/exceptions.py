class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class BadRequest(AppException):
    def __init__(self, message: str = "Bad request", code: str | None = None):
        super().__init__(message, 400, code)


class NotFound(AppException):
    def __init__(self, message: str = "Not found", code: str | None = None):
        super().__init__(message, 404, code)
