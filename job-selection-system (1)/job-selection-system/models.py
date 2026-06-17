from extensions import db
from datetime import datetime, timezone
from flask_login import UserMixin


class User(UserMixin, db.Model):
    """Пользователь"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='job_seeker')
    company_name = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    skills = db.relationship('UserSkill', back_populates='user', cascade='all, delete-orphan')
    applications = db.relationship('Application', back_populates='applicant', cascade='all, delete-orphan')
    posted_vacancies = db.relationship('Vacancy', back_populates='employer', cascade='all, delete-orphan')

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
        """Общее количество откликов на все вакансии работодателя"""
        if not self.is_employer:
            return 0
        total = 0
        for vacancy in self.posted_vacancies:
            total += len(vacancy.applications)
        return total

class Skill(db.Model):
    """Навык"""
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    vacancies = db.relationship('VacancySkill', back_populates='skill', cascade='all, delete-orphan')
    users = db.relationship('UserSkill', back_populates='skill', cascade='all, delete-orphan')


class Vacancy(db.Model):
    """Вакансия"""
    __tablename__ = 'vacancies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    description = db.Column(db.Text)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    location = db.Column(db.String(100))
    url = db.Column(db.String(200))
    employer_phone = db.Column(db.String(20), nullable=True)
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # исправлено

    skills = db.relationship('VacancySkill', back_populates='vacancy', cascade='all, delete-orphan')
    applications = db.relationship('Application', back_populates='vacancy', cascade='all, delete-orphan')
    employer = db.relationship('User', back_populates='posted_vacancies')


class VacancySkill(db.Model):
    """Связь вакансии и навыка"""
    __tablename__ = 'vacancy_skills'

    id = db.Column(db.Integer, primary_key=True)
    vacancy_id = db.Column(db.Integer, db.ForeignKey('vacancies.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)

    vacancy = db.relationship('Vacancy', back_populates='skills')
    skill = db.relationship('Skill', back_populates='vacancies')

    __table_args__ = (db.UniqueConstraint('vacancy_id', 'skill_id'),)


class UserSkill(db.Model):
    """Связь пользователя и навыка"""
    __tablename__ = 'user_skills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)

    user = db.relationship('User', back_populates='skills')
    skill = db.relationship('Skill', back_populates='users')

    __table_args__ = (db.UniqueConstraint('user_id', 'skill_id'),)


class Application(db.Model):
    """Отклик на вакансию"""
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    vacancy_id = db.Column(db.Integer, db.ForeignKey('vacancies.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status_updated_at = db.Column(db.DateTime, nullable=True)  # Добавьте это поле

    vacancy = db.relationship('Vacancy', back_populates='applications')
    applicant = db.relationship('User', back_populates='applications')

    __table_args__ = (db.UniqueConstraint('vacancy_id', 'applicant_id'),)

    @property
    def status_rus(self):
        """Русское название статуса"""
        statuses = {
            'pending': 'На рассмотрении',
            'accepted': 'Принят',
            'rejected': 'Отклонён'
        }
        return statuses.get(self.status, self.status)