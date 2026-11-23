class AppException(Exception):
    """Базовый класс исключений приложения."""


class InvalidRangeError(AppException):
    """Запрошен некорректный или выходящий за пределы файла диапазон байтов."""