from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from extensions import db, bcrypt
from models import User, UserSkill, Skill, Application, Vacancy
from forms import RegistrationForm, LoginForm, ProfileInfoForm, ProfileSkillsForm, VacancyAddForm, VacancyEditForm, ApplicationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Этот email уже зарегистрирован', 'danger')
            return render_template('register.html', form=form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

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
        login_user(user)
        flash(f'Добро пожаловать, {user.first_name}! Регистрация прошла успешно.', 'success')
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
    """Профиль пользователя"""
    info_form = ProfileInfoForm()
    skills_form = ProfileSkillsForm()

    if info_form.validate_on_submit() and 'first_name' in request.form:
        current_user.first_name = info_form.first_name.data
        current_user.last_name = info_form.last_name.data
        current_user.phone = info_form.phone.data

        try:
            db.session.commit()
            flash('Основная информация обновлена!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'danger')

        return redirect(url_for('auth.profile'))

    if skills_form.validate_on_submit() and 'skills' in request.form:
        if current_user.is_job_seeker and skills_form.skills.data:
            UserSkill.query.filter_by(user_id=current_user.id).delete()

            skills_list = [s.strip() for s in skills_form.skills.data.split(',') if s.strip()]
            for skill_name in skills_list:
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                    db.session.flush()

                user_skill = UserSkill(user_id=current_user.id, skill_id=skill.id)
                db.session.add(user_skill)

            try:
                db.session.commit()
                flash('Навыки успешно обновлены!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при сохранении: {str(e)}', 'danger')

        return redirect(url_for('auth.profile'))

    elif request.method == 'GET':
        info_form.first_name.data = current_user.first_name
        info_form.last_name.data = current_user.last_name
        info_form.phone.data = current_user.phone

        if current_user.is_job_seeker:
            skills_list = [us.skill.name for us in current_user.skills]
            skills_form.skills.data = ', '.join(skills_list)

    return render_template('profile.html',
                           info_form=info_form,
                           skills_form=skills_form,
                           user=current_user)

@auth_bp.route('/post-vacancy', methods=['GET', 'POST'])
@login_required
def post_vacancy():
    if not current_user.is_authenticated:
        flash('Войдите чтобы разместить вакансию', 'warning')
        return redirect(url_for('auth.login'))

    form = VacancyAddForm()
    if form.validate_on_submit():
        from models import Vacancy, Skill, VacancySkill

        vacancy = Vacancy(
            title=form.title.data,
            company=form.company.data,
            description=form.description.data,
            salary_min=form.salary_min.data,
            salary_max=form.salary_max.data,
            location=form.location.data,
            employer_phone=form.employer_phone.data,
            posted_by=current_user.id
        )
        db.session.add(vacancy)
        db.session.flush()

        if form.skills.data:
            skills_list = [s.strip() for s in form.skills.data.split(',') if s.strip()]
            for skill_name in skills_list:
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                    db.session.flush()

                vacancy_skill = VacancySkill(vacancy_id=vacancy.id, skill_id=skill.id)
                db.session.add(vacancy_skill)

        db.session.commit()
        flash('Вакансия опубликована', 'success')
        return redirect(url_for('auth.my_vacancies'))

    return render_template('post_vacancy.html', form=form)


@auth_bp.route('/edit-vacancy/<int:vacancy_id>', methods=['GET', 'POST'])
@login_required
def edit_vacancy(vacancy_id):
    from models import Vacancy, Skill, VacancySkill
    from forms import VacancyEditForm

    vacancy = Vacancy.query.get_or_404(vacancy_id)

    if vacancy.posted_by != current_user.id:
        flash('У вас нет прав для редактирования этой вакансии', 'danger')
        return redirect(url_for('index'))

    form = VacancyEditForm()

    if form.validate_on_submit():
        if form.cancel.data:
            return redirect(url_for('auth.my_vacancies'))

        vacancy.title = form.title.data
        vacancy.company = form.company.data
        vacancy.description = form.description.data
        vacancy.salary_min = form.salary_min.data
        vacancy.salary_max = form.salary_max.data
        vacancy.location = form.location.data
        vacancy.employer_phone = form.employer_phone.data

        if form.skills.data:
            VacancySkill.query.filter_by(vacancy_id=vacancy.id).delete()

            skills_list = [s.strip() for s in form.skills.data.split(',') if s.strip()]
            for skill_name in skills_list:
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                    db.session.flush()

                vacancy_skill = VacancySkill(vacancy_id=vacancy.id, skill_id=skill.id)
                db.session.add(vacancy_skill)

        try:
            db.session.commit()
            flash('Вакансия успешно обновлена!', 'success')
            return redirect(url_for('auth.my_vacancies'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'danger')

    elif request.method == 'GET':
        form.title.data = vacancy.title
        form.company.data = vacancy.company
        form.description.data = vacancy.description
        form.salary_min.data = vacancy.salary_min
        form.salary_max.data = vacancy.salary_max
        form.location.data = vacancy.location
        form.employer_phone.data = vacancy.employer_phone

        skills_list = [vs.skill.name for vs in vacancy.skills]
        form.skills.data = ', '.join(skills_list)

    return render_template('edit_vacancy.html', form=form, vacancy=vacancy)


@auth_bp.route('/delete-vacancy/<int:vacancy_id>', methods=['POST'])
@login_required
def delete_vacancy(vacancy_id):
    """Удаление вакансии"""
    from models import Vacancy, Application

    vacancy = Vacancy.query.get_or_404(vacancy_id)

    if vacancy.posted_by != current_user.id:
        flash('У вас нет прав для удаления этой вакансии', 'danger')
        return redirect(url_for('index'))

    applications_count = Application.query.filter_by(vacancy_id=vacancy.id).count()

    if applications_count > 0:
        flash(f'Невозможно удалить вакансию: на неё уже откликнулись {applications_count} кандидатов', 'warning')
        return redirect(url_for('auth.my_vacancies'))

    try:
        db.session.delete(vacancy)
        db.session.commit()
        flash('Вакансия успешно удалена', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')

    return redirect(url_for('auth.my_vacancies'))

@auth_bp.route('/my-vacancies')
@login_required
def my_vacancies():
    """Вакансии работодателя"""
    if not current_user.is_employer:
        flash('Эта страница только для работодателей', 'warning')
        return redirect(url_for('index'))

    vacancies = Vacancy.query.filter_by(posted_by=current_user.id).all()
    return render_template('my_vacancies.html', vacancies=vacancies)


@auth_bp.route('/my-applications')
@login_required
def my_applications():
    """Отклики соискателя с детальной информацией"""
    if not current_user.is_job_seeker:
        flash('Эта страница только для соискателей', 'warning')
        return redirect(url_for('index'))

    from models import Application
    from matcher import SkillMatcher, normalize_text, get_model

    applications = Application.query.filter_by(
        applicant_id=current_user.id
    ).order_by(Application.created_at.desc()).all()

    matcher = SkillMatcher()
    vacancies_list = [app.vacancy for app in applications]
    matcher.prepare(vacancies_list)

    profile_skills_list = [us.skill.name for us in current_user.skills]
    user_skills = matcher.get_user_skills_from_profile(profile_skills_list)

    user_skills_text = ', '.join(profile_skills_list)
    normalized_input = normalize_text(user_skills_text)
    model = get_model()

    try:
        if normalized_input.strip():
            query_embedding = model.encode(normalized_input)
        else:
            query_embedding = None
    except Exception as e:
        logger.error(f"Ошибка создания эмбеддинга запроса: {e}")
        query_embedding = None

    for app in applications:
        app.match_percentage = matcher.calculate_full_match_percentage(
            user_skills,
            app.vacancy,
            query_embedding
        )
        vacancy_skills = [vs.skill.name for vs in app.vacancy.skills]
        app.missing_skills = matcher.get_missing_skills(user_skills, vacancy_skills)

        app.recommendations = matcher.generate_recommendations_from_vacancies(
            user_skills,
            vacancy_skills,
            vacancies_list
        )

        app.can_withdraw = (app.status == 'pending')

    stats = {
        'total': len(applications),
        'pending': len([a for a in applications if a.status == 'pending']),
        'accepted': len([a for a in applications if a.status == 'accepted']),
        'rejected': len([a for a in applications if a.status == 'rejected'])
    }

    return render_template('my_applications.html',
                           applications=applications,
                           stats=stats)

@auth_bp.route('/vacancy/<int:vacancy_id>/applications')
@login_required
def vacancy_applications(vacancy_id):
    """Отклики на вакансию (для работодателя)"""
    vacancy = Vacancy.query.get_or_404(vacancy_id)

    if vacancy.posted_by != current_user.id:
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    return render_template('vacancy_applications.html', vacancy=vacancy)


@auth_bp.route('/application/<int:application_id>/<action>')
@login_required
def handle_application(application_id, action):
    """Обработка отклика"""
    from datetime import datetime

    application = Application.query.get_or_404(application_id)

    if application.vacancy.posted_by != current_user.id:
        flash('У вас нет доступа к этому действию', 'danger')
        return redirect(url_for('index'))

    if action == 'accept':
        application.status = 'accepted'
        application.status_updated_at = datetime.utcnow()
        flash('Отклик принят', 'success')
    elif action == 'reject':
        application.status = 'rejected'
        application.status_updated_at = datetime.utcnow()
        flash('Отклик отклонен', 'info')

    db.session.commit()
    return redirect(url_for('auth.vacancy_applications', vacancy_id=application.vacancy_id))


@auth_bp.route('/vacancy/<int:vacancy_id>/apply', methods=['POST'])
@login_required
def apply_to_vacancy(vacancy_id):
    """Отклик на вакансию"""
    if not current_user.is_job_seeker:
        flash('Только соискатели могут откликаться на вакансии', 'warning')
        return redirect(url_for('index'))

    from models import Vacancy, Application
    from forms import ApplicationForm

    vacancy = Vacancy.query.get_or_404(vacancy_id)

    existing = Application.query.filter_by(
        vacancy_id=vacancy_id,
        applicant_id=current_user.id
    ).first()

    if existing:
        flash('Вы уже откликались на эту вакансию', 'warning')
        return redirect(url_for('vacancy_detail', vacancy_id=vacancy_id))

    form = ApplicationForm()
    if form.validate_on_submit():
        application = Application(
            vacancy_id=vacancy_id,
            applicant_id=current_user.id,
            cover_letter=form.cover_letter.data
        )
        db.session.add(application)
        db.session.commit()

        flash('Отклик успешно отправлен!', 'success')
        return redirect(url_for('auth.my_applications'))

    flash('Ошибка при отправке отклика', 'danger')
    return redirect(url_for('vacancy_detail', vacancy_id=vacancy_id))


@auth_bp.route('/withdraw-application/<int:application_id>', methods=['POST'])
@login_required
def withdraw_application(application_id):
    """Отзыв отклика на вакансию"""
    from models import Application

    application = Application.query.get_or_404(application_id)

    if application.applicant_id != current_user.id:
        flash('У вас нет прав для этого действия', 'danger')
        return redirect(url_for('index'))

    if application.status != 'pending':
        flash('Нельзя отозвать уже обработанный отклик', 'warning')
        return redirect(url_for('auth.my_applications'))

    try:
        db.session.delete(application)
        db.session.commit()
        flash('Отклик успешно отозван', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при отзыве отклика: {str(e)}', 'danger')

    return redirect(url_for('auth.my_applications'))