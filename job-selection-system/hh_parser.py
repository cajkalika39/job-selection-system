import requests
import time
from extensions import db  # Импортируем только db, не модели


class HHParser:
    """Парсер вакансий с hh.ru"""

    API_URL = "https://api.hh.ru/vacancies"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'JobSelectionSystem/1.0 (job.selection@example.com)'
        })

    def search_vacancies(self, search_query, area=113, pages=1):
        """
        Поиск вакансий по ключевому слову

        Args:
            search_query: ключевое слово для поиска (например, "Python")
            area: регион (1 - Москва, 2 - СПб, 113 - Россия)
            pages: количество страниц для парсинга (по 20 вакансий на странице)

        Returns:
            list: список обработанных вакансий
        """
        all_vacancies = []

        for page in range(pages):
            params = {
                'text': search_query,
                'area': area,
                'page': page,
                'per_page': 20,
                'search_field': 'name',
                'order_by': 'publication_time'
            }

            try:
                print(f"📡 Запрос к API: {self.API_URL} с параметрами {params}")
                response = self.session.get(self.API_URL, params=params)
                response.raise_for_status()

                data = response.json()
                items = data.get('items', [])
                print(f"✅ Получен ответ, найдено вакансий: {len(items)}")

                vacancies = self._parse_vacancies(items)
                all_vacancies.extend(vacancies)

                print(f"✅ Страница {page + 1}: обработано {len(vacancies)} вакансий")

                # Задержка между запросами, чтобы не нагружать API
                time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                print(f"❌ Ошибка при запросе: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"   Статус: {e.response.status_code}")
                    print(f"   Ответ: {e.response.text[:200]}")
                break

        return all_vacancies

    def _parse_vacancies(self, items):
        """Парсинг списка вакансий из JSON ответа"""
        vacancies = []

        for item in items:
            try:
                # Получаем описание и требования
                name = item.get('name', '')
                snippet = item.get('snippet', {})
                requirement_text = snippet.get('requirement', '') or ''
                responsibility_text = snippet.get('responsibility', '') or ''

                # Объединяем все текстовые поля для поиска навыков
                full_text = f"{name} {requirement_text} {responsibility_text}".lower()

                # Извлекаем ключевые навыки из текста
                extracted_skills = self._extract_skills_from_text(full_text)

                # Добавляем Python в навыки, если он есть в названии, но не был найден
                if 'python' in name.lower() and 'Python' not in extracted_skills:
                    extracted_skills.append('Python')

                # Получаем информацию о зарплате
                salary = item.get('salary')
                salary_min, salary_max, currency = self._parse_salary(salary)

                # Получаем название компании
                employer = item.get('employer', {})
                company_name = employer.get('name') if employer else None

                # Получаем локацию
                area = item.get('area', {})
                location = area.get('name') if area else None

                vacancy_data = {
                    'title': item.get('name'),
                    'company': company_name,
                    'description': f"Требования: {requirement_text}\n\nОбязанности: {responsibility_text}"[:5000],
                    'salary_min': salary_min,
                    'salary_max': salary_max,
                    'currency': currency or 'RUB',
                    'location': location,
                    'url': item.get('alternate_url'),
                    'skills': extracted_skills,
                    'hh_id': item.get('id')
                }

                # Пропускаем вакансии без названия
                if vacancy_data['title']:
                    vacancies.append(vacancy_data)
                    print(f"  ✓ Обработана: {vacancy_data['title'][:50]}... (навыков: {len(extracted_skills)})")

            except Exception as e:
                print(f"⚠️ Ошибка при парсинге вакансии: {e}")
                continue

        return vacancies

    def _parse_salary(self, salary):
        """Парсинг информации о зарплате"""
        if not salary:
            return None, None, 'RUB'

        salary_from = salary.get('from')
        salary_to = salary.get('to')
        currency = salary.get('currency', 'RUB')

        return salary_from, salary_to, currency

    def _extract_skills_from_text(self, text):
        """
        Извлечение навыков из текста с улучшенным поиском
        """
        if not text:
            return []

        text = text.lower()
        found_skills = []

        # Расширенный словарь навыков с ключевыми словами для поиска
        skill_patterns = {
            'Python': ['python', 'питон', 'пайтон'],
            'Java': ['java', 'джава'],
            'JavaScript': ['javascript', 'js', 'ecmascript'],
            'TypeScript': ['typescript', 'ts'],
            'C++': ['c++', 'c plus plus', 'си плюс плюс'],
            'C#': ['c#', 'c sharp', 'си шарп'],
            'PHP': ['php'],
            'Ruby': ['ruby'],
            'Go': ['go', 'golang'],
            'Rust': ['rust'],

            'Flask': ['flask', 'фласк'],
            'Django': ['django', 'джанго'],
            'FastAPI': ['fastapi', 'fast api'],
            'React': ['react', 'reactjs', 'react.js'],
            'Vue': ['vue', 'vuejs', 'vue.js'],
            'Angular': ['angular', 'angularjs'],

            'SQL': ['sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'oracle', 'база данных'],
            'PostgreSQL': ['postgresql', 'postgres'],
            'MySQL': ['mysql'],
            'MongoDB': ['mongodb', 'mongo'],
            'Redis': ['redis'],

            'Git': ['git', 'гит'],
            'Docker': ['docker', 'докер'],
            'Kubernetes': ['kubernetes', 'k8s', 'кубернетес'],
            'Linux': ['linux', 'линукс'],

            'REST API': ['rest', 'rest api', 'restful'],
            'GraphQL': ['graphql'],

            'OOP': ['oop', 'объектно ориентированное', 'объектно-ориентированное'],
            'TDD': ['tdd', 'test driven'],

            'AWS': ['aws', 'amazon web services'],
            'Azure': ['azure'],
            'GCP': ['gcp', 'google cloud'],

            'HTML': ['html'],
            'CSS': ['css'],
            'Bootstrap': ['bootstrap'],

            'Data Science': ['data science', 'ds'],
            'Machine Learning': ['machine learning', 'ml', 'машинное обучение'],
            'Pandas': ['pandas'],
            'NumPy': ['numpy'],
            'Scikit-learn': ['scikit-learn', 'sklearn']
        }

        for skill, keywords in skill_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    found_skills.append(skill)
                    break

        # Удаляем дубликаты, сохраняя порядок
        seen = set()
        unique_skills = []
        for skill in found_skills:
            if skill not in seen:
                seen.add(skill)
                unique_skills.append(skill)

        return unique_skills

    def save_vacancies_to_db(self, vacancies_data):
        """
        Сохранение вакансий в базу данных

        Args:
            vacancies_data: список словарей с данными вакансий

        Returns:
            int: количество сохраненных вакансий
        """
        # Импортируем модели внутри метода, чтобы избежать циклического импорта
        from models import Skill, Vacancy, VacancySkill

        saved_count = 0

        for vac_data in vacancies_data:
            try:
                # Проверяем, есть ли уже такая вакансия (по ID или URL)
                existing = None
                if vac_data.get('hh_id'):
                    existing = Vacancy.query.filter_by(hh_id=vac_data['hh_id']).first()
                if not existing and vac_data.get('url'):
                    existing = Vacancy.query.filter_by(url=vac_data['url']).first()

                if existing:
                    print(f"⏭️ Вакансия уже существует: {vac_data['title']}")
                    continue

                # Создаем новую вакансию
                vacancy = Vacancy(
                    title=vac_data['title'],
                    company=vac_data['company'],
                    description=vac_data['description'],
                    salary_min=vac_data['salary_min'],
                    salary_max=vac_data['salary_max'],
                    currency=vac_data['currency'] or 'RUB',
                    location=vac_data['location'],
                    url=vac_data['url'],
                    hh_id=vac_data.get('hh_id')
                )

                db.session.add(vacancy)
                db.session.flush()  # Чтобы получить ID вакансии

                # Добавляем навыки
                for skill_name in vac_data['skills']:
                    # Ищем или создаем навык
                    skill = Skill.query.filter_by(name=skill_name).first()
                    if not skill:
                        skill = Skill(name=skill_name)
                        db.session.add(skill)
                        db.session.flush()

                    # Проверяем, не добавлен ли уже этот навык
                    existing_skill = VacancySkill.query.filter_by(
                        vacancy_id=vacancy.id,
                        skill_id=skill.id
                    ).first()

                    if not existing_skill:
                        # Связываем навык с вакансией
                        vacancy_skill = VacancySkill(
                            vacancy_id=vacancy.id,
                            skill_id=skill.id
                        )
                        db.session.add(vacancy_skill)

                saved_count += 1
                print(f"💾 Сохранена вакансия: {vac_data['title']} (навыков: {len(vac_data['skills'])})")

                # Каждые 10 вакансий делаем коммит
                if saved_count % 10 == 0:
                    db.session.commit()
                    print(f"📦 Промежуточный коммит: сохранено {saved_count} вакансий")

            except Exception as e:
                print(f"❌ Ошибка при сохранении вакансии {vac_data.get('title')}: {e}")
                db.session.rollback()
                continue

        # Финальный коммит
        try:
            db.session.commit()
            print(f"✅ Всего сохранено: {saved_count} вакансий")
        except Exception as e:
            print(f"❌ Ошибка при финальном коммите: {e}")
            db.session.rollback()

        return saved_count