class NotForSendError(Exception):
    """Не для пересылки в Телеграм."""

    pass


class EmptyResponseError(NotForSendError):
    """Ответ от API пустой."""

    pass


class TelegramSendError(NotForSendError):
    """Ошибка отправки сообщения в Телеграм."""

    pass


class InvalidResponseCodeError(Exception):
    """Неверный код ответа API."""

    pass
