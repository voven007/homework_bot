
class ApiStatusNotOkException(Exception):
    """Ответ сервера не равен 200."""


class ApiException(Exception):
    """Ошибка сервера."""


class IsNotFindKeyException(Exception):
    """Не найден ключ в домашней работе."""
