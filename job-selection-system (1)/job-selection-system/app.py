from flask import Flask, render_template, request, flash, url_for, redirect
from flask_login import current_user, login_required
from config import Config
from extensions import db, login_manager, bcrypt
from matcher import SkillMatcher, clean_skills_input
from resume_parser import ResumeParser
from werkzeug.utils import secure_filename
from pathlib import Path
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return db.session.get(User, int(user_id))

    from auth import auth_bp
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    @app.route('/', methods=['GET', 'POST'])
    def index():
        results = None
        skills_value = request.args.get('skills', '')

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'resume':
                if 'resume' not in request.files:
                    flash('Файл не выбран', 'danger')
                    return redirect(url_for('index'))

                file = request.files['resume']
                if file.filename == '':
                    flash('Файл не выбран', 'danger')
                    return redirect(url_for('index'))

                if file and allowed_file(file.filename):
                    filename = secure_filename(
                        f"{current_user.id}_{file.filename}" if current_user.is_authenticated else file.filename)
                    filepath = Config.UPLOAD_FOLDER / filename
                    file.save(filepath)

                    try:
                        parser = ResumeParser()
                        parsed_data = parser.parse_resume(filepath)
                        skills_text = ', '.join(parsed_data['skills'])

                        if current_user.is_authenticated and current_user.is_job_seeker:
                            from models import Skill, UserSkill

                            for skill_name in parsed_data['skills']:
                                skill = Skill.query.filter_by(name=skill_name).first()
                                if not skill:
                                    skill = Skill(name=skill_name)
                                    db.session.add(skill)
                                    db.session.flush()

                                existing = UserSkill.query.filter_by(
                                    user_id=current_user.id,
                                    skill_id=skill.id
                                ).first()
                                if not existing:
                                    user_skill = UserSkill(user_id=current_user.id, skill_id=skill.id)
                                    db.session.add(user_skill)

                            db.session.commit()
                            flash(f'✅ Из резюме извлечено {len(parsed_data["skills"])} навыков и добавлено в профиль!',
                                  'success')
                            return redirect(url_for('index', skills=skills_text))
                        else:
                            flash(f'📄 Из резюме извлечены навыки: {", ".join(parsed_data["skills"])}', 'info')
                            return render_template('index.html', results=None, skills_value=skills_text)

                    except Exception as e:
                        flash(f'❌ Ошибка при обработке резюме: {str(e)}', 'danger')
                    finally:
                        if filepath.exists():
                            filepath.unlink()
                else:
                    flash('❌ Неподдерживаемый формат файла. Используйте PDF или DOCX.', 'danger')

                return redirect(url_for('index'))

            search_skills = request.form.get('skills', '')
            search_skills = clean_skills_input(search_skills)
            use_profile = request.form.get('use_profile_skills') == 'true'

            final_skills = search_skills

            if current_user.is_authenticated and use_profile:
                profile_skills_list = [us.skill.name for us in current_user.skills]
                if profile_skills_list:
                    profile_skills_text = ', '.join(profile_skills_list)
                    if search_skills:
                        final_skills = f"{profile_skills_text}, {search_skills}"
                    else:
                        final_skills = profile_skills_text
                        flash(f'Используются навыки из профиля: {profile_skills_text}', 'info')

            if not final_skills:
                flash('Введите навыки для поиска или используйте навыки из профиля', 'warning')
                return render_template('index.html', results=results, skills_value=search_skills)

            from models import Vacancy

            location = request.form.get('location', '').strip()
            keywords = request.form.get('keywords', '').strip()

            query = Vacancy.query

            if location and location != 'Вся Россия':
                query = query.filter(Vacancy.location.ilike(f'%{location}%'))

            if keywords:
                query = query.filter(
                    Vacancy.title.ilike(f'%{keywords}%') |
                    Vacancy.description.ilike(f'%{keywords}%')
                )

            all_vacancies = query.all()

            if all_vacancies:
                matcher = SkillMatcher()
                results = matcher.match_vacancies(final_skills, all_vacancies)
                for result in results:
                    user_skills = matcher.parse_user_skills(final_skills)
                    vacancy_skills = [vs.skill.name for vs in result['vacancy'].skills]
                    result['recommendations'] = matcher.generate_recommendations_from_vacancies(
                        user_skills, vacancy_skills, all_vacancies
                    )
                flash(f'Найдено {len(results)} вакансий', 'success')
            else:
                flash('Вакансии не найдены...', 'warning')

        return render_template('index.html', results=results, skills_value=skills_value)

    @app.route('/upload-resume', methods=['POST'])
    @login_required
    def upload_resume():
        file = request.files['resume']
        filename = secure_filename(f"{current_user.id}_{file.filename}")
        filepath = Config.UPLOAD_FOLDER / filename
        file.save(filepath)

        parser = ResumeParser()
        parsed_data = parser.parse_resume(filepath)
        skills_text = ', '.join(parsed_data['skills'])

        from models import Skill, UserSkill
        for skill_name in parsed_data['skills']:
            skill = Skill.query.filter_by(name=skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
                db.session.flush()
            existing = UserSkill.query.filter_by(user_id=current_user.id, skill_id=skill.id).first()
            if not existing:
                user_skill = UserSkill(user_id=current_user.id, skill_id=skill.id)
                db.session.add(user_skill)
        db.session.commit()

        filepath.unlink()
        flash(f'✅ Из резюме извлечено {len(parsed_data["skills"])} навыков и добавлено в профиль!', 'success')
        return redirect(url_for('index', skills=skills_text))

    @app.route('/vacancy/<int:vacancy_id>')
    def vacancy_detail(vacancy_id):
        from models import Vacancy
        from forms import ApplicationForm

        vacancy = Vacancy.query.get_or_404(vacancy_id)
        form = ApplicationForm()

        has_applied = False
        if current_user.is_authenticated and current_user.is_job_seeker:
            from models import Application
            application = Application.query.filter_by(
                vacancy_id=vacancy_id,
                applicant_id=current_user.id
            ).first()
            has_applied = application is not None

        return render_template('vacancy_detail.html',
                               vacancy=vacancy,
                               form=form,
                               has_applied=has_applied)

    return app


application = create_app()

if __name__ == '__main__':
    application.run(debug=True)