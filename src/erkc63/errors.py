# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025-2026 Sergey Dudanov <sergey.dudanov@gmail.com>


class ErkcError(Exception):
    """Базовое исключение"""


class ParsingError(ErkcError):
    """Ошибка обработки данных"""


class ErkcApiError(ErkcError):
    """Базовая ошибка API"""


class AccountBindingError(ErkcApiError):
    """Ошибка привязки/отвязки лицевого счета"""


class AuthenticationError(ErkcApiError):
    """Ошибка аутентификации"""


class AuthenticationRequired(ErkcApiError):
    """Ошибка отсутствия аутентификации"""


class AccountNotFound(ErkcApiError):
    """Лицевой счет не найден"""


class SessionRequired(ErkcApiError):
    """Ошибка отсутствия открытой сессии"""
