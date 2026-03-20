import os
from pathlib import Path


class Config:
    """Базовая конфигурация приложения"""

    # Секретный ключ для защиты от CSRF и подписей сессий
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-key-for-development'

    # Настройки базы данных
    basedir = Path(__file__).parent.absolute()

    # Создаем папку instance, если её нет
    instance_path = basedir / 'instance'
    os.makedirs(instance_path, exist_ok=True)

    # Используем SQLite с абсолютным путем
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              f'sqlite:///{instance_path / "site.db"}'

    # Отключаем отслеживание изменений (для экономии ресурсов)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Папка для загруженных файлов (резюме)
    UPLOAD_FOLDER = basedir / 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Максимальный размер файла 16MB