class AppError(Exception):
    """Базовый класс исключений приложения."""


class InvalidRangeError(AppError):
    """Запрошен некорректный или выходящий за пределы файла диапазон байтов."""
