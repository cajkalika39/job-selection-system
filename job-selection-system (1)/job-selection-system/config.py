from pathlib import Path

class Config:
    SECRET_KEY = 'hard-to-guess-key-for-development'

    BASEDIR = Path(__file__).parent.absolute()
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASEDIR / "site.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = BASEDIR / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}

    UPLOAD_FOLDER.mkdir(exist_ok=True)