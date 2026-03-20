from extensions import db
from datetime import datetime
from flask_login import UserMixin


class User(UserMixin, db.Model):
    """Модель пользователя (соискателя или работодателя)"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    company_name = db.Column(db.String(100), nullable=True)  # Для работодателей
    company_description = db.Column(db.Text, nullable=True)  # Описание компании
    company_website = db.Column(db.String(100), nullable=True)  # Сайт компании
    company_logo = db.Column(db.String(200), nullable=True)  # Путь к логотипу
    phone = db.Column(db.String(20), nullable=True)

    # Роль пользователя: 'job_seeker' или 'employer'
    role = db.Column(db.String(20), nullable=False, default='job_seeker')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Связь с навыками пользователя (только для соискателей)
    skills = db.relationship('UserSkill', back_populates='user', cascade='all, delete-orphan')

    # Связь с откликами на вакансии (для соискателей)
    applications = db.relationship('Application', back_populates='applicant',
                                   foreign_keys='Application.applicant_id',
                                   cascade='all, delete-orphan')

    # Связь с размещенными вакансиями (для работодателей)
    posted_vacancies = db.relationship('Vacancy', back_populates='employer',
                                       foreign_keys='Vacancy.posted_by',
                                       cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_employer(self):
        return self.role == 'employer'

    @property
    def is_job_seeker(self):
        return self.role == 'job_seeker'

    @property
    def total_applications_received(self):
        """Количество откликов на все вакансии работодателя"""
        total = 0
        for vacancy in self.posted_vacancies:
            total += len(vacancy.applications)
        return total


class Skill(db.Model):
    """Модель навыка (например: Python, SQL, Flask)"""
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50))  # Например: "backend", "frontend", "database"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    vacancies = db.relationship('VacancySkill', back_populates='skill', cascade='all, delete-orphan')
    users = db.relationship('UserSkill', back_populates='skill', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Skill {self.name}>'


class Vacancy(db.Model):
    """Модель вакансии"""
    __tablename__ = 'vacancies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    description = db.Column(db.Text)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    currency = db.Column(db.String(3), default='RUB')
    location = db.Column(db.String(100))
    url = db.Column(db.String(200))
    hh_id = db.Column(db.String(50), unique=True, nullable=True)

    # Кто разместил вакансию (если это работодатель)
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с навыками вакансии
    skills = db.relationship('VacancySkill', back_populates='vacancy', cascade='all, delete-orphan')

    # Связь с откликами
    applications = db.relationship('Application', back_populates='vacancy',
                                   cascade='all, delete-orphan')

    # Отношение к работодателю
    employer = db.relationship('User', back_populates='posted_vacancies',
                               foreign_keys=[posted_by])

    def __repr__(self):
        return f'<Vacancy {self.title}>'

    @property
    def required_skills_count(self):
        return len(self.skills)

    @property
    def applications_count(self):
        return len(self.applications)


class VacancySkill(db.Model):
    """Связующая таблица между вакансиями и навыками (многие-ко-многим)"""
    __tablename__ = 'vacancy_skills'

    id = db.Column(db.Integer, primary_key=True)
    vacancy_id = db.Column(db.Integer, db.ForeignKey('vacancies.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    importance = db.Column(db.Integer, default=1)  # Важность навыка (1-5), можно использовать для весов

    # Отношения
    vacancy = db.relationship('Vacancy', back_populates='skills')
    skill = db.relationship('Skill', back_populates='vacancies')

    # Уникальность пары (чтобы не было дубликатов)
    __table_args__ = (db.UniqueConstraint('vacancy_id', 'skill_id', name='unique_vacancy_skill'),)


class UserSkill(db.Model):
    """Связующая таблица между пользователями и навыками"""
    __tablename__ = 'user_skills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    level = db.Column(db.Integer, default=1)  # Уровень владения (1-5)

    # Отношения
    user = db.relationship('User', back_populates='skills')
    skill = db.relationship('Skill', back_populates='users')

    # Уникальность пары
    __table_args__ = (db.UniqueConstraint('user_id', 'skill_id', name='unique_user_skill'),)


class Application(db.Model):
    """Модель отклика на вакансию"""
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    vacancy_id = db.Column(db.Integer, db.ForeignKey('vacancies.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Отношения
    vacancy = db.relationship('Vacancy', back_populates='applications')
    applicant = db.relationship('User', back_populates='applications',
                                foreign_keys=[applicant_id])

    __table_args__ = (db.UniqueConstraint('vacancy_id', 'applicant_id',
                                          name='unique_application'),)

    @property
    def status_rus(self):
        statuses = {
            'pending': 'Ожидает рассмотрения',
            'accepted': 'Принят',
            'rejected': 'Отклонен'
        }
        return statuses.get(self.status, self.status)