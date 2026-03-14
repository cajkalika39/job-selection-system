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

2. Создать виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows

3. Установить зависимости:
```bash
pip install -r requirements.txt

4. Создать файл .env из примера:
```bash
cp .env.example .env
# Отредактировать .env, указав свои настройки

5. Инициализировать базу данных:
```bash
python scripts/init_db.py
python scripts/seed_data.py

6. Запустить приложение:
```bash
python run.py

## Запуск через Docker
```bash
docker-compose up -d

## 📚 Документация
- **Схема базы данных**
- **API документация**
- **Инструкция по деплою**

## 🤝 Участие в разработке
1. Fork репозитория
2. Создайте ветку для фичи (git checkout -b feature/amazing-feature)
3. Commit изменений (git commit -m 'Add amazing feature')
4. Push в ветку (git push origin feature/amazing-feature)
5. Open Pull Request

## 📄 Лицензия
MIT License - см. файл LICENSE

## 👥 Авторы
Команда разработчиков - Название команды
