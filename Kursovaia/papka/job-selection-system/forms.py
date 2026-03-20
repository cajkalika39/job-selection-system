from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Optional, NumberRange, Email, EqualTo, Length, ValidationError
from flask_wtf.file import FileField, FileAllowed


class RegistrationForm(FlaskForm):
    """Форма регистрации"""
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль',
                                     validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Я хочу',
                       choices=[
                           ('job_seeker', 'Найти работу'),
                           ('employer', 'Найти сотрудников')
                       ],
                       validators=[DataRequired()])
    company_name = StringField('Название компании', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Зарегистрироваться')

    def validate_company_name(form, field):
        if form.role.data == 'employer' and not field.data:
            raise ValidationError('Название компании обязательно для работодателя')


class LoginForm(FlaskForm):
    """Форма входа"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class VacancySearchForm(FlaskForm):
    """Форма для поиска вакансий через API"""
    search_query = StringField('Ключевое слово',
                               validators=[DataRequired()],
                               render_kw={"placeholder": "например: Python"})

    area = SelectField('Регион',
                       choices=[
                           ('113', 'Вся Россия'),
                           ('1', 'Москва'),
                           ('2', 'Санкт-Петербург'),
                           ('3', 'Екатеринбург'),
                           ('4', 'Новосибирск'),
                           ('88', 'Казань'),
                           ('66', 'Нижний Новгород'),
                           ('10', 'Самара'),
                           ('76', 'Ростов-на-Дону'),
                           ('40', 'Пермь'),
                           ('28', 'Воронеж'),
                           ('77', 'Краснодар'),
                           ('78', 'Саратов'),
                           ('71', 'Тюмень'),
                           ('22', 'Красноярск'),
                           ('30', 'Волгоград'),
                           ('26', 'Ижевск'),
                           ('31', 'Иркутск'),
                           ('32', 'Йошкар-Ола'),
                           ('34', 'Калининград'),
                           ('35', 'Калуга'),
                           ('36', 'Кемерово'),
                           ('37', 'Киров'),
                           ('38', 'Кострома'),
                           ('41', 'Курск'),
                           ('43', 'Липецк'),
                           ('45', 'Магнитогорск'),
                           ('47', 'Мурманск'),
                           ('50', 'Омск'),
                           ('51', 'Орел'),
                           ('52', 'Оренбург'),
                           ('53', 'Пенза'),
                           ('55', 'Псков'),
                           ('57', 'Рязань'),
                           ('60', 'Смоленск'),
                           ('62', 'Ставрополь'),
                           ('63', 'Сыктывкар'),
                           ('64', 'Тамбов'),
                           ('65', 'Тверь'),
                           ('67', 'Томск'),
                           ('68', 'Тула'),
                           ('69', 'Ульяновск'),
                           ('70', 'Уфа'),
                           ('72', 'Хабаровск'),
                           ('73', 'Чебоксары'),
                           ('74', 'Челябинск'),
                           ('75', 'Чита'),
                           ('79', 'Ярославль')
                       ],
                       default='113')

    pages = IntegerField('Количество страниц (по 20 вакансий)',
                         validators=[Optional(), NumberRange(min=1, max=5)],
                         default=2)

    submit = SubmitField('Найти и сохранить вакансии')


class VacancyAddForm(FlaskForm):
    """Форма для ручного добавления вакансии (для работодателей)"""
    title = StringField('Название вакансии', validators=[DataRequired()])
    company = StringField('Компания', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    salary_min = IntegerField('Зарплата от', validators=[Optional()])
    salary_max = IntegerField('Зарплата до', validators=[Optional()])
    location = StringField('Локация', validators=[Optional()])
    skills = StringField('Требуемые навыки (через запятую)', validators=[Optional()])
    submit = SubmitField('Опубликовать вакансию')


class ApplicationForm(FlaskForm):
    """Форма отклика на вакансию"""
    cover_letter = TextAreaField('Сопроводительное письмо',
                                 validators=[Optional(), Length(max=2000)],
                                 render_kw={"rows": 5})
    submit = SubmitField('Откликнуться')


class ProfileForm(FlaskForm):
    """Форма редактирования профиля"""
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    company_name = StringField('Название компании', validators=[Optional(), Length(max=100)])
    company_description = TextAreaField('Описание компании', validators=[Optional(), Length(max=1000)])
    company_website = StringField('Сайт компании', validators=[Optional(), Length(max=100)])
    company_logo = FileField('Логотип компании', validators=[FileAllowed(['jpg', 'png', 'svg'], 'Только изображения!')])
    skills = TextAreaField('Навыки (через запятую)', validators=[Optional()])
    resume = FileField('Загрузить резюме (PDF)', validators=[FileAllowed(['pdf'], 'Только PDF!')])
    submit = SubmitField('Сохранить профиль')