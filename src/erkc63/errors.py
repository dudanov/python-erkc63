class ErkcError(Exception):
    pass


class ParsingError(ErkcError):
    pass


class ApiError(ErkcError):
    pass


class AccountBindingError(ApiError):
    pass


class AuthenticationError(ApiError):
    pass


class AuthenticationRequired(ApiError):
    pass


class AccountNotFound(ApiError):
    pass


class SessionRequired(ApiError):
    pass
