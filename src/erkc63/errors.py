# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025-2026 Sergey Dudanov <sergey.dudanov@gmail.com>

class ErkcError(Exception):
    """Базовое исключение"""


class ParsingError(ErkcError):
    """Ошибка обработки данных"""


class ApiError(ErkcError):
    """Базовая ошибка API"""


class AccountBindingError(ApiError):
    """Ошибка привязки/отвязки лицевого счета"""


class AuthenticationError(ApiError):
    """Ошибка аутентификации"""


class AuthenticationRequired(ApiError):
    """Ошибка отсутствия аутентификации"""


class AccountNotFound(ApiError):
    """Лицевой счет не найден"""


class SessionRequired(ApiError):
    """Ошибка отсутствия открытой сессии"""
