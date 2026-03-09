class AppError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundException(AppError):
    pass


class ConflictError(AppError):
    pass


class ValidationError(AppError):
    pass


class ForbiddenError(AppError):
    pass
