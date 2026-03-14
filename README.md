# 🎯 Job Matching System

Система подбора вакансий на основе навыков. Пользователь вводит свои навыки или загружает резюме, 
а система находит наиболее подходящие вакансии с указанием процента совпадения и рекомендациями.

## ✨ Возможности

- 🔐 **Регистрация и авторизация** пользователей
- 📄 **Загрузка резюме** (PDF, DOCX) с автоматическим извлечением навыков
- 🔍 **Поиск вакансий** по навыкам с расчетом процента совпадения
- 🤖 **Автоматический парсинг** вакансий с hh.ru, LinkedIn, Indeed
- 📊 **Аналитика** востребованных навыков и рекомендации по развитию
- ⚡ **Фоновые задачи** для регулярного обновления базы вакансий
- 📱 **Адаптивный дизайн** для мобильных устройств

## 🛠 Технологии

- **Backend:** Python 3.10+, Flask, SQLAlchemy
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript, Chart.js
- **База данных:** MySQL / SQLite
- **Парсинг:** HH.ru API, JobSpy (LinkedIn/Indeed)
- **Деплой:** Docker, Nginx, Gunicorn

## 📦 Установка и запуск

### Локальная установка

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/yourusername/job-matching-system.git
   cd job-matching-system
   ```

2. Создать виртуальное окружение:
   ```bash
   python -m venv venv
   ```
   
   Для Linux/Mac:
   ```bash
   source venv/bin/activate
   ```
   
   Для Windows:
   ```bash
   venv\Scripts\activate
   ```

3. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создать файл .env из примера:
   ```bash
   cp .env.example .env
   ```
   
   Отредактируйте `.env` файл, указав свои настройки:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=mysql+pymysql://user:password@localhost/db_name
   ```

5. Инициализировать базу данных:
   ```bash
   python scripts/init_db.py
   python scripts/seed_data.py
   ```

6. Запустить приложение:
   ```bash
   python run.py
   ```

   Приложение будет доступно по адресу: `http://localhost:5000`

### Запуск через Docker

1. Убедитесь, что установлены Docker и Docker Compose

2. Запустите контейнеры:
   ```bash
   docker-compose up -d
   ```

3. Приложение будет доступно по адресу: `http://localhost`

4. Остановка контейнеров:
   ```bash
   docker-compose down
   ```

## 📚 Документация

- [Схема базы данных](docs/database.md)
- [API документация](docs/api.md)
- [Инструкция по деплою](docs/deployment.md)

## 🤝 Участие в разработке

1. Сделайте форк (Fork) репозитория
2. Создайте ветку для новой функции:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Зафиксируйте изменения:
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. Отправьте изменения в свой форк:
   ```bash
   git push origin feature/amazing-feature
   ```
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE)

## 👥 Авторы

- Команда разработчиков - [Название команды]

## 📊 Структура проекта

```
job-matching-system/
├── app/                    # Основное приложение
│   ├── models/             # Модели базы данных
│   ├── routes/             # Маршруты
│   ├── services/           # Бизнес-логика
│   ├── scrapers/           # Парсеры вакансий
│   ├── tasks/              # Фоновые задачи
│   ├── templates/          # HTML шаблоны
│   └── static/             # CSS, JS, изображения
├── scripts/                # Вспомогательные скрипты
├── tests/                  # Тесты
├── docs/                   # Документация
├── config.py               # Конфигурация
├── run.py                  # Точка входа
├── requirements.txt        # Зависимости
├── Dockerfile              # Для Docker
└── docker-compose.yml      # Docker Compose
```
