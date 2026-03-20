from app import app
from extensions import db
from models import Vacancy, Skill, VacancySkill


def seed_database():
    """Наполнение базы данных тестовыми вакансиями"""
    with app.app_context():
        # Очищаем существующие данные (опционально)
        # VacancySkill.query.delete()
        # Vacancy.query.delete()
        # Skill.query.delete()

        # Создаем навыки
        skills_data = [
            {'name': 'Python', 'category': 'backend'},
            {'name': 'Flask', 'category': 'backend'},
            {'name': 'Django', 'category': 'backend'},
            {'name': 'SQL', 'category': 'database'},
            {'name': 'PostgreSQL', 'category': 'database'},
            {'name': 'Git', 'category': 'tools'},
            {'name': 'Docker', 'category': 'devops'},
            {'name': 'JavaScript', 'category': 'frontend'},
            {'name': 'React', 'category': 'frontend'},
            {'name': 'HTML', 'category': 'frontend'},
            {'name': 'CSS', 'category': 'frontend'},
            {'name': 'REST API', 'category': 'backend'}
        ]

        skills = {}
        for skill_data in skills_data:
            skill = Skill.query.filter_by(name=skill_data['name']).first()
            if not skill:
                skill = Skill(**skill_data)
                db.session.add(skill)
                db.session.flush()
            skills[skill_data['name']] = skill

        # Создаем вакансии
        vacancies_data = [
            {
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'description': 'Ищем опытного Python разработчика для работы над высоконагруженными проектами',
                'salary_min': 150000,
                'salary_max': 250000,
                'location': 'Москва',
                'skills': ['Python', 'Flask', 'SQL', 'Git', 'Docker']
            },
            {
                'title': 'Full Stack Developer',
                'company': 'Web Studio',
                'description': 'Разработка современных веб-приложений на Python и JavaScript',
                'salary_min': 120000,
                'salary_max': 200000,
                'location': 'Санкт-Петербург',
                'skills': ['Python', 'JavaScript', 'React', 'Flask', 'SQL', 'Git']
            },
            {
                'title': 'Backend Developer',
                'company': 'FinTech Solutions',
                'description': 'Разработка банковских систем и API',
                'salary_min': 180000,
                'salary_max': 300000,
                'location': 'Москва',
                'skills': ['Python', 'Django', 'PostgreSQL', 'REST API', 'Git', 'Docker']
            },
            {
                'title': 'Junior Python Developer',
                'company': 'Startup Hub',
                'description': 'Отличная возможность для начинающего разработчика',
                'salary_min': 80000,
                'salary_max': 120000,
                'location': 'Казань',
                'skills': ['Python', 'Flask', 'SQL', 'Git']
            }
        ]

        for vac_data in vacancies_data:
            # Проверяем, есть ли уже такая вакансия
            existing = Vacancy.query.filter_by(title=vac_data['title'], company=vac_data['company']).first()
            if existing:
                continue

            skills_list = vac_data.pop('skills')
            vacancy = Vacancy(**vac_data)
            db.session.add(vacancy)
            db.session.flush()

            # Добавляем навыки к вакансии
            for skill_name in skills_list:
                skill = skills.get(skill_name)
                if skill:
                    vacancy_skill = VacancySkill(
                        vacancy_id=vacancy.id,
                        skill_id=skill.id
                    )
                    db.session.add(vacancy_skill)

        db.session.commit()
        print("✅ Тестовые данные успешно добавлены!")


if __name__ == '__main__':
    seed_database()