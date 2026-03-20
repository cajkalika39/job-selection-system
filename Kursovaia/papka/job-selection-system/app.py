from flask import Flask, render_template, request, flash, url_for, redirect
from flask_login import current_user
from config import Config
from extensions import db, login_manager, bcrypt
from forms import VacancySearchForm, VacancyAddForm, ApplicationForm, ProfileForm
from hh_parser import HHParser
from matcher import SkillMatcher
from models import User
import os


def create_app():
    """Фабрика приложений Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализируем расширения
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Настройка login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Импортируем и регистрируем blueprint для аутентификации
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    # Импортируем модели (чтобы SQLAlchemy знал о них)
    with app.app_context():
        from models import User, Skill, Vacancy, VacancySkill, UserSkill, Application
        # Проверяем, что папка instance существует
        print(f"📁 База данных будет создана по пути: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # Создаем таблицы
        db.create_all()
        print("✅ База данных создана/проверена!")

    @app.route('/', methods=['GET', 'POST'])
    def index():
        """Главная страница с подбором вакансий"""
        results = None

        if request.method == 'POST':
            action = request.form.get('action', '')

            # Обработка формы с навыками
            if action == 'skills' and 'skills' in request.form and request.form['skills']:
                skills_text = request.form['skills']
                region = request.form.get('region', '113')
                keywords = request.form.get('keywords', '')

                # Получаем все вакансии из БД
                from models import Vacancy
                vacancies = Vacancy.query.all()

                if vacancies:
                    # Создаем экземпляр матчера и подбираем вакансии
                    matcher = SkillMatcher()
                    results = matcher.match_vacancies(skills_text, vacancies)

                    flash(f'✅ Найдено {len(results)} вакансий, подходящих под ваши навыки', 'success')
                else:
                    flash('⚠️ В базе данных пока нет вакансий. Сначала добавьте вакансии через hh.ru или вручную.',
                          'warning')

            # Обработка загруженного файла
            elif action == 'resume' and 'resume' in request.files:
                file = request.files['resume']
                if file and file.filename:
                    filename = file.filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                    # Здесь будет парсинг резюме
                    flash(f'✅ Файл {filename} загружен. Функция парсинга резюме в разработке.', 'info')

            else:
                flash('⚠️ Пожалуйста, введите навыки или загрузите файл', 'warning')

        return render_template('index.html', results=results)

    @app.route('/vacancy/<int:vacancy_id>', methods=['GET', 'POST'])
    def vacancy_detail(vacancy_id):
        """Страница вакансии с возможностью отклика"""
        from models import Vacancy, Application

        vacancy = Vacancy.query.get_or_404(vacancy_id)
        form = ApplicationForm()

        # Проверяем, откликался ли уже пользователь
        has_applied = False
        if current_user.is_authenticated and current_user.is_job_seeker:
            has_applied = Application.query.filter_by(
                vacancy_id=vacancy.id,
                applicant_id=current_user.id
            ).first() is not None

        if form.validate_on_submit():
            if not current_user.is_authenticated:
                flash('Пожалуйста, войдите чтобы откликнуться', 'warning')
                return redirect(url_for('auth.login', next=request.url))

            if not current_user.is_job_seeker:
                flash('Только соискатели могут откликаться на вакансии', 'warning')
                return redirect(url_for('vacancy_detail', vacancy_id=vacancy.id))

            if has_applied:
                flash('Вы уже откликались на эту вакансию', 'info')
            else:
                application = Application(
                    vacancy_id=vacancy.id,
                    applicant_id=current_user.id,
                    cover_letter=form.cover_letter.data
                )
                db.session.add(application)
                db.session.commit()
                flash('Отклик отправлен!', 'success')
                return redirect(url_for('vacancy_detail', vacancy_id=vacancy.id))

        return render_template('vacancy_detail.html',
                               vacancy=vacancy,
                               form=form,
                               has_applied=has_applied)

    @app.route('/vacancies')
    def vacancies():
        """Страница со списком всех вакансий"""
        from models import Vacancy
        vacancies_list = Vacancy.query.all()
        return render_template('vacancies.html', vacancies=vacancies_list)

    @app.route('/post-vacancy', methods=['GET', 'POST'])
    def post_vacancy():
        """Размещение вакансии (только для работодателей)"""
        if not current_user.is_authenticated or not current_user.is_employer:
            flash('Только работодатели могут размещать вакансии', 'warning')
            return redirect(url_for('auth.login'))

        form = VacancyAddForm()
        form.company.data = current_user.company_name  # Подставляем компанию пользователя

        if form.validate_on_submit():
            from models import Vacancy, Skill, VacancySkill

            vacancy = Vacancy(
                title=form.title.data,
                company=form.company.data,
                description=form.description.data,
                salary_min=form.salary_min.data,
                salary_max=form.salary_max.data,
                location=form.location.data,
                posted_by=current_user.id
            )

            db.session.add(vacancy)
            db.session.flush()

            # Добавляем навыки
            if form.skills.data:
                skills_list = [s.strip() for s in form.skills.data.split(',') if s.strip()]
                for skill_name in skills_list:
                    skill = Skill.query.filter_by(name=skill_name).first()
                    if not skill:
                        skill = Skill(name=skill_name)
                        db.session.add(skill)
                        db.session.flush()

                    vacancy_skill = VacancySkill(
                        vacancy_id=vacancy.id,
                        skill_id=skill.id
                    )
                    db.session.add(vacancy_skill)

            db.session.commit()

            flash(f'✅ Вакансия "{form.title.data}" опубликована!', 'success')
            return redirect(url_for('auth.my_vacancies'))

        return render_template('post_vacancy.html', form=form)

    return app


# Создаем экземпляр приложения
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)