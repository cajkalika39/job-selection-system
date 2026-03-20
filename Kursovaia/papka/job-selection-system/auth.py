from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from extensions import db
from models import User, UserSkill, Skill, Application, Vacancy
from forms import RegistrationForm, LoginForm, ProfileForm
from flask_bcrypt import Bcrypt
import os

bcrypt = Bcrypt()
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Проверяем, не занят ли email
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Этот email уже зарегистрирован', 'danger')
            return render_template('register.html', form=form)

        # Создаем хеш пароля
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # Создаем пользователя
        user = User(
            email=form.email.data,
            password_hash=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=form.role.data,
            company_name=form.company_name.data if form.role.data == 'employer' else None
        )

        db.session.add(user)
        db.session.commit()

        # Сразу логиним пользователя после регистрации
        login_user(user)
        flash(f'Добро пожаловать, {user.first_name}! Регистрация прошла успешно.', 'success')

        # Перенаправляем на главную страницу
        return redirect(url_for('index'))

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'С возвращением, {user.first_name}!', 'success')

            # Перенаправляем на главную страницу или на запрошенную страницу
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Профиль пользователя с возможностью редактирования"""
    form = ProfileForm()

    if form.validate_on_submit():
        print("Форма валидна, сохраняем данные...")  # Отладка

        # Обновляем основную информацию
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data

        if current_user.is_employer:
            current_user.company_name = form.company_name.data
            current_user.company_description = form.company_description.data
            current_user.company_website = form.company_website.data

            # Обрабатываем загрузку логотипа
            if form.company_logo.data:
                filename = f"logo_{current_user.id}.{form.company_logo.data.filename.split('.')[-1]}"
                form.company_logo.data.save(os.path.join('uploads', filename))
                current_user.company_logo = filename

        # Обрабатываем навыки ТОЛЬКО для соискателей
        if current_user.is_job_seeker and form.skills.data:
            print(f"Сохраняем навыки: {form.skills.data}")  # Отладка

            # Удаляем старые навыки
            UserSkill.query.filter_by(user_id=current_user.id).delete()

            # Парсим новые навыки
            skills_list = [s.strip() for s in form.skills.data.split(',') if s.strip()]
            print(f"Список навыков: {skills_list}")  # Отладка

            for skill_name in skills_list:
                # Ищем или создаем навык
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                    db.session.flush()
                    print(f"Создан новый навык: {skill_name}")  # Отладка

                # Добавляем связь
                user_skill = UserSkill(
                    user_id=current_user.id,
                    skill_id=skill.id
                )
                db.session.add(user_skill)
                print(f"Добавлена связь: пользователь {current_user.id} - навык {skill.id}")  # Отладка

        # Обрабатываем загрузку резюме (для соискателей)
        if current_user.is_job_seeker and form.resume.data:
            filename = f"resume_{current_user.id}.pdf"
            form.resume.data.save(os.path.join('uploads', filename))
            flash('Резюме загружено', 'success')

        try:
            db.session.commit()
            print("Изменения сохранены в БД")  # Отладка
            flash('Профиль успешно обновлен!', 'success')
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")  # Отладка
            db.session.rollback()
            flash('Ошибка при сохранении профиля', 'danger')

        return redirect(url_for('auth.profile'))

    # Заполняем форму текущими данными
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone

        if current_user.is_employer:
            form.company_name.data = current_user.company_name
            form.company_description.data = current_user.company_description
            form.company_website.data = current_user.company_website

        # Заполняем навыки ТОЛЬКО для соискателей
        if current_user.is_job_seeker:
            skills_list = [us.skill.name for us in current_user.skills]
            form.skills.data = ', '.join(skills_list)
            print(f"Загружены навыки: {form.skills.data}")  # Отладка

    return render_template('profile.html', form=form, user=current_user)


@auth_bp.route('/my-vacancies')
@login_required
def my_vacancies():
    """Вакансии, размещенные работодателем"""
    if not current_user.is_employer:
        flash('Эта страница только для работодателей', 'warning')
        return redirect(url_for('index'))

    vacancies = Vacancy.query.filter_by(posted_by=current_user.id).all()
    return render_template('my_vacancies.html', vacancies=vacancies)


@auth_bp.route('/my-applications')
@login_required
def my_applications():
    """Отклики соискателя"""
    if not current_user.is_job_seeker:
        flash('Эта страница только для соискателей', 'warning')
        return redirect(url_for('index'))

    applications = Application.query.filter_by(applicant_id=current_user.id).all()
    return render_template('my_applications.html', applications=applications)


@auth_bp.route('/vacancy/<int:vacancy_id>/applications')
@login_required
def vacancy_applications(vacancy_id):
    """Отклики на конкретную вакансию (для работодателя)"""
    vacancy = Vacancy.query.get_or_404(vacancy_id)

    # Проверяем, что это вакансия текущего работодателя
    if vacancy.posted_by != current_user.id:
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    return render_template('vacancy_applications.html', vacancy=vacancy)


@auth_bp.route('/application/<int:application_id>/<action>')
@login_required
def handle_application(application_id, action):
    """Обработка отклика (принять/отклонить)"""
    application = Application.query.get_or_404(application_id)

    # Проверяем, что это вакансия текущего работодателя
    if application.vacancy.posted_by != current_user.id:
        flash('У вас нет доступа к этому действию', 'danger')
        return redirect(url_for('index'))

    if action == 'accept':
        application.status = 'accepted'
        flash('Отклик принят', 'success')
    elif action == 'reject':
        application.status = 'rejected'
        flash('Отклик отклонен', 'info')

    db.session.commit()
    return redirect(url_for('auth.vacancy_applications', vacancy_id=application.vacancy_id))