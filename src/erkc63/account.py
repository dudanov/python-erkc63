import dataclasses as dc
from decimal import Decimal


@dc.dataclass
class PublicAccountInfo:
    """Открытая информация о лицевом счете."""

    account: int
    """Номер лицевого счета"""
    address: str
    """Адрес"""
    balance: Decimal
    """Задолженность"""
    peni: Decimal
    """Пени"""

    def __repr__(self) -> str:
        return (
            f"Лицевой счет:  {self.account}\n"
            f"Адрес:         {self.address}\n"
            f"Задолженность: {self.balance}\n"
            f"Пени:          {self.peni}\n"
        )


@dc.dataclass
class AccountInfo:
    """Информация о лицевом счете"""

    address: str
    """Адрес"""
    person: str
    """Собственник"""
    phone: str
    """Телефон"""
    email: str
    """Электронная почта"""
    account: int
    """Лицевой счет"""
    square: Decimal
    """Общая площадь"""
    registered: int
    """Зарегистрировано"""
    hosted: int
    """Проживает"""
    document: str
    """Право собственности"""
