class ErkcError(Exception):
    pass


class ParsingError(ErkcError):
    pass


class ApiError(ErkcError):
    pass


class AccountBindingError(ApiError):
    pass


class AuthorizationError(ApiError):
    pass


class AuthorizationRequired(ApiError):
    pass


class SessionRequired(ApiError):
    pass


class AccountNotFound(ApiError):
    pass
