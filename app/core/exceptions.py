class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(
        self, message: str, *, status_code: int | None = None, code: str | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class UnsupportedFileTypeError(AppError):
    status_code = 415
    code = "unsupported_file_type"


class ConfigurationError(AppError):
    status_code = 500
    code = "configuration_error"


class ExternalServiceError(AppError):
    status_code = 503
    code = "external_service_error"
