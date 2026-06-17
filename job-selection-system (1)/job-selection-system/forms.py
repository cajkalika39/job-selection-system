from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length
from flask_wtf.file import FileField, FileAllowed


class RegistrationForm(FlaskForm):
    """Регистрация"""
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Я хочу', choices=[
        ('job_seeker', 'Найти работу'),
        ('employer', 'Найти сотрудников')
    ])
    company_name = StringField('Название компании', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    """Вход"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class VacancyAddForm(FlaskForm):
    """Добавление вакансии"""
    title = StringField('Название', validators=[DataRequired()])
    company = StringField('Компания', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    salary_min = IntegerField('Зарплата от', validators=[Optional()])
    salary_max = IntegerField('Зарплата до', validators=[Optional()])
    location = StringField('Локация', validators=[Optional()])
    employer_phone = StringField('Контактный телефон', validators=[Optional()])
    skills = StringField('Навыки (через запятую)', validators=[Optional()])
    submit = SubmitField('Опубликовать')


class ApplicationForm(FlaskForm):
    """Отклик на вакансию"""
    cover_letter = TextAreaField('Сопроводительное письмо', validators=[Optional()])
    submit = SubmitField('Откликнуться')


class ProfileInfoForm(FlaskForm):
    """Форма для основной информации"""
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Сохранить изменения')


class ProfileSkillsForm(FlaskForm):
    """Форма для навыков"""
    skills = TextAreaField('Навыки (через запятую)', validators=[Optional()])
    submit = SubmitField('Сохранить навыки')


class VacancyEditForm(FlaskForm):
    """Форма редактирования вакансии"""
    title = StringField('Название', validators=[DataRequired()])
    company = StringField('Компания', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    salary_min = IntegerField('Зарплата от', validators=[Optional()])
    salary_max = IntegerField('Зарплата до', validators=[Optional()])
    location = StringField('Локация', validators=[Optional()])
    employer_phone = StringField('Контактный телефон', validators=[Optional()])
    skills = StringField('Навыки (через запятую)', validators=[Optional()])
    submit = SubmitField('Сохранить изменения')
    cancel = SubmitField('Отмена')