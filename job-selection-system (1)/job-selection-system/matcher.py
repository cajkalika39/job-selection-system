from sentence_transformers import SentenceTransformer, util
from pymorphy3 import MorphAnalyzer
import re
import warnings
from typing import List, Set, Dict
import logging

warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

_model_instance = None
_morph_instance = None


def get_model() -> SentenceTransformer:
    global _model_instance
    if _model_instance is None:
        try:
            logger.info("Загрузка модели SentenceTransformer...")
            _model_instance = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Модель успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            try:
                _model_instance = SentenceTransformer('all-MiniLM-L6-v2')
                logger.warning("Используется fallback модель all-MiniLM-L6-v2")
            except:
                raise RuntimeError("Не удалось загрузить ни одну модель SentenceTransformer")
    return _model_instance


def get_morph() -> MorphAnalyzer:
    global _morph_instance
    if _morph_instance is None:
        logger.info("Загрузка морфологического анализатора pymorphy3...")
        _morph_instance = MorphAnalyzer()
        logger.info("Морфологический анализатор загружен")
    return _morph_instance


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r'[^\w\s#+]', ' ', text)

    words = text.split()
    normalized = []
    morph = get_morph()

    for word in words:
        if word:
            if '#' in word or '++' in word:
                normalized.append(word)
            else:
                try:
                    parsed = morph.parse(word)[0]
                    normalized.append(parsed.normal_form)
                except Exception as e:
                    logger.debug(f"Ошибка морфологического разбора слова '{word}': {e}")
                    normalized.append(word)

    return " ".join(normalized)


def calculate_skill_match(user_skills: Set[str], vacancy_skills: List[str]) -> tuple:
    """Расчет совпадения навыков с весами"""
    if not vacancy_skills:
        return 0, [], []

    user_set = set(user_skills)
    vacancy_set = set(vacancy_skills)

    exact_only_skills = {'1с', '1c', 'c#', 'c++', 'php', 'sql'}

    exact_matches = set()
    for user_skill in user_set:
        for vac_skill in vacancy_set:
            if vac_skill.lower() in exact_only_skills:
                if user_skill.lower() == vac_skill.lower():
                    exact_matches.add(vac_skill)
            else:
                if user_skill.lower() == vac_skill.lower():
                    exact_matches.add(vac_skill)

    partial_matches = set()
    for user_skill in user_set:
        for vac_skill in vacancy_set:
            if vac_skill.lower() in exact_only_skills:
                continue
            if user_skill in vac_skill or vac_skill in user_skill:
                if user_skill not in exact_matches and vac_skill not in exact_matches:
                    partial_matches.add(vac_skill)

    all_matches = exact_matches | partial_matches
    missing = vacancy_set - all_matches

    match_score = len(exact_matches) * 1.0 + len(partial_matches) * 0.5
    total_score = len(vacancy_set) * 1.0

    percent = (match_score / total_score) * 100 if total_score > 0 else 0

    return percent, list(all_matches), list(missing)


def calculate_semantic_similarity(query_embedding, text_embedding) -> float:
    """Расчет косинусного сходства между эмбеддингами"""
    if query_embedding is None or text_embedding is None:
        return 0.0
    similarity = util.cos_sim(query_embedding, text_embedding).item()
    return max(0.0, similarity)


def prepare_vacancies(vacancies_from_db: List) -> List[Dict]:
    """Подготовка вакансий: нормализация текста и создание эмбеддингов"""
    model = get_model()

    vacancies = []

    for vacancy in vacancies_from_db:
        skills_list = []
        for vs in vacancy.skills:
            try:
                normalized_skill = normalize_text(vs.skill.name)
                skills_list.append(normalized_skill)
            except Exception as e:
                logger.debug(f"Ошибка нормализации навыка: {e}")
                skills_list.append(vs.skill.name.lower())

        title_norm = normalize_text(vacancy.title) if vacancy.title else ""
        description_norm = normalize_text(vacancy.description) if vacancy.description else ""
        skills_text = " ".join(skills_list)

        combined_text = f"{title_norm} {description_norm} {skills_text}"

        try:
            if title_norm:
                title_embedding = model.encode(title_norm)
            else:
                title_embedding = None

            combined_embedding = model.encode(combined_text) if combined_text.strip() else None
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддинга для вакансии {vacancy.id}: {e}")
            combined_embedding = None
            title_embedding = None

        vacancies.append({
            "id": vacancy.id,
            "vacancy": vacancy,
            "skills": skills_list,
            "title_norm": title_norm,
            "combined_embedding": combined_embedding,
            "title_embedding": title_embedding
        })

    return vacancies


def build_skill_keywords(vacancies: List[Dict]) -> Dict[str, List[str]]:
    """Построение словаря ключевых слов для поиска навыков"""
    skill_keywords = {}

    for v in vacancies:
        for skill in v["skills"]:
            if skill not in skill_keywords:
                variations = set([skill])

                if len(skill) > 3:
                    if skill.endswith("ние"):
                        variations.add(skill[:-3] + "ть")
                    elif skill.endswith("ка"):
                        variations.add(skill[:-2] + "ть")
                    elif skill.endswith("щик"):
                        variations.add(skill[:-3] + "ка")
                    elif skill.endswith("ание"):
                        variations.add(skill[:-4] + "ать")

                skill_keywords[skill] = list(variations)

    return skill_keywords


def extract_skills(text: str, skill_keywords: Dict[str, List[str]]) -> Set[str]:
    if not text or not skill_keywords:
        return set()

    text = text.lower()
    found = set()

    for skill, keywords in skill_keywords.items():
        for keyword in keywords:
            if keyword in text:
                found.add(skill)
                break

    return found


def clean_skills_input(text: str) -> str:
    """Очистка ввода навыков от лишних слов"""
    if not text:
        return ""

    stop_phrases = [
        'я умею работать в', 'я знаю', 'умею работать с',
        'владею', 'знание', 'опыт работы с', 'навыки',
        'skills', 'умею', 'могу', 'имею опыт'
    ]

    text_lower = text.lower()
    for phrase in stop_phrases:
        text_lower = text_lower.replace(phrase, '')

    text_lower = text_lower.replace(' и ', ', ')
    text_lower = text_lower.replace(' и', ',')
    text_lower = text_lower.replace('и ', ',')

    parts = text_lower.split(',')
    skills = []
    for part in parts:
        part = part.strip()
        if len(part) > 1 and part != 'и' and not part.isdigit():
            skills.append(part)

    text_lower = ', '.join(skills)

    corrections = {
        'exсel': 'excel',
        'ексель': 'excel',
        'ексел': 'excel',
        'ворд': 'word',
        'вoрд': 'word',
        'повер поинт': 'powerpoint',
        'питон': 'python',
        'джава': 'java',
        'c#': 'c#',
        'c++': 'c++',
        'джанго': 'django',
        'фласк': 'flask',
    }

    words = [w.strip() for w in text_lower.split(',')]
    cleaned_words = []
    for word in words:
        if len(word) < 2:
            continue
        word_clean = word
        for wrong, correct in corrections.items():
            if wrong in word_clean:
                word_clean = word_clean.replace(wrong, correct)
        cleaned_words.append(word_clean)

    return ', '.join(cleaned_words)

def calculate_candidate_match_for_vacancy(candidate, vacancy) -> Dict:
    candidate_skills = set()
    if hasattr(candidate, 'skills'):
        for us in candidate.skills:
            candidate_skills.add(us.skill.name)

    vacancy_skills = []
    if hasattr(vacancy, 'skills'):
        vacancy_skills = [vs.skill.name for vs in vacancy.skills]

    if not vacancy_skills:
        return {
            'match_percentage': 0,
            'matched_skills': [],
            'missing_skills': [],
            'candidate_skills': list(candidate_skills)
        }

    match_percent, matched, missing = calculate_skill_match(
        candidate_skills, vacancy_skills
    )

    return {
        'match_percentage': round(match_percent, 2),
        'matched_skills': list(matched),
        'missing_skills': list(missing),
        'candidate_skills': list(candidate_skills)
    }


def rank_candidates_for_vacancy(vacancy, applications) -> List[Dict]:
    ranked = []

    for app in applications:
        candidate = app.applicant

        match_data = calculate_candidate_match_for_vacancy(candidate, vacancy)

        ranked.append({
            'application': app,
            'applicant': candidate,
            'match_percentage': match_data['match_percentage'],
            'matched_skills': match_data['matched_skills'],
            'missing_skills': match_data['missing_skills'],
            'candidate_skills': match_data['candidate_skills']
        })

    ranked.sort(key=lambda x: x['match_percentage'], reverse=True)

    for i, item in enumerate(ranked, 1):
        item['rank'] = i

    return ranked


class SkillMatcher:
    """Продвинутый матчер с использованием семантического поиска"""

    def __init__(self):
        self.skill_keywords = {}
        self.prepared_vacancies = []

    def prepare(self, vacancies_from_db: List) -> None:
        """Подготовка данных для поиска"""
        if not vacancies_from_db:
            self.prepared_vacancies = []
            self.skill_keywords = {}
            return

        self.prepared_vacancies = prepare_vacancies(vacancies_from_db)
        self.skill_keywords = build_skill_keywords(self.prepared_vacancies)
        logger.info(f"Подготовлено {len(self.prepared_vacancies)} вакансий для поиска")

    def match_vacancies(self, user_skills_input: str, vacancies_from_db: List) -> List[Dict]:
        """Подбор вакансий - семантика только если есть совпадения"""
        self.prepare(vacancies_from_db)

        if not self.prepared_vacancies:
            return []

        normalized_input = normalize_text(user_skills_input)

        model = get_model()

        try:
            if normalized_input.strip():
                query_embedding = model.encode(normalized_input)
            else:
                query_embedding = None
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддинга запроса: {e}")
            query_embedding = None

        user_skills = extract_skills(normalized_input, self.skill_keywords)

        results = []
        for v in self.prepared_vacancies:
            skill_match_percent, matched_skills, missing_skills = calculate_skill_match(
                user_skills, v["skills"]
            )
            skill_score = skill_match_percent / 100

            if skill_match_percent > 0:
                semantic_score = 0
                if query_embedding is not None and v["combined_embedding"] is not None:
                    semantic_score = calculate_semantic_similarity(query_embedding, v["combined_embedding"])

                title_score = 0
                if query_embedding is not None and v["title_embedding"] is not None:
                    title_score = calculate_semantic_similarity(query_embedding, v["title_embedding"])

                final_percent = (
                                        skill_score * 0.7 +
                                        semantic_score * 0.2 +
                                        title_score * 0.1
                                ) * 100
            else:
                semantic_score = 0
                if query_embedding is not None and v["combined_embedding"] is not None:
                    semantic_score = calculate_semantic_similarity(query_embedding, v["combined_embedding"])
                final_percent = min(semantic_score * 10, 10)

            if len(missing_skills) == 0 and len(v["skills"]) > 0:
                final_percent = 100

            results.append({
                'vacancy': v["vacancy"],
                'match_percentage': round(final_percent, 2),
                'matched_skills': matched_skills,
                'missing_skills': missing_skills
            })

        results.sort(key=lambda x: x['match_percentage'], reverse=True)
        return results

    def parse_user_skills(self, skills_input: str) -> Set[str]:
        """Парсит навыки из строки"""
        if not skills_input:
            return set()
        cleaned = clean_skills_input(skills_input)
        return set([s.strip().lower() for s in cleaned.split(',') if s.strip()])

    def get_user_skills_from_profile(self, profile_skills_list: List[str]) -> Set[str]:
        """Получает навыки пользователя из профиля через тот же механизм, что и при поиске"""
        if not profile_skills_list:
            return set()

        if self.skill_keywords:
            user_skills_text = ', '.join(profile_skills_list)
            normalized_input = normalize_text(user_skills_text)
            user_skills = extract_skills(normalized_input, self.skill_keywords)
            return user_skills
        else:
            user_skills_text = ', '.join(profile_skills_list)
            return self.parse_user_skills(user_skills_text)

    def calculate_match_percentage(self, user_skills: Set[str], vacancy_skills: List) -> float:
        """Рассчитывает процент совпадения (только навыки)"""
        percent, _, _ = calculate_skill_match(user_skills, vacancy_skills)
        return percent

    def calculate_full_match_percentage(self, user_skills: Set[str], vacancy, query_embedding=None) -> float:
        """
        Полный расчет процента совпадения с учетом семантики и заголовка
        """
        prepared = prepare_vacancies([vacancy])
        if not prepared:
            return 0

        v = prepared[0]

        if query_embedding is None:
            user_skills_text = ', '.join(user_skills)
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

        if query_embedding is None:
            skill_match_percent, _, missing = calculate_skill_match(user_skills, v["skills"])
            if len(missing) == 0 and len(v["skills"]) > 0:
                return 100.0
            return round(skill_match_percent, 2)

        skill_match_percent, matched_skills, missing_skills = calculate_skill_match(user_skills, v["skills"])
        skill_score = skill_match_percent / 100

        if skill_match_percent > 0:
            semantic_score = 0
            if query_embedding is not None and v["combined_embedding"] is not None:
                semantic_score = calculate_semantic_similarity(query_embedding, v["combined_embedding"])

            title_score = 0
            if query_embedding is not None and v["title_embedding"] is not None:
                title_score = calculate_semantic_similarity(query_embedding, v["title_embedding"])

            final_percent = (skill_score * 0.7 + semantic_score * 0.2 + title_score * 0.1) * 100
        else:
            semantic_score = 0
            if query_embedding is not None and v["combined_embedding"] is not None:
                semantic_score = calculate_semantic_similarity(query_embedding, v["combined_embedding"])
            final_percent = min(semantic_score * 10, 10)

        if len(missing_skills) == 0 and len(v["skills"]) > 0:
            final_percent = 100

        return round(final_percent, 2)

    def get_missing_skills(self, user_skills: Set[str], vacancy_skills: List) -> List[str]:
        """Определяет недостающие навыки"""
        _, _, missing = calculate_skill_match(user_skills, vacancy_skills)
        return missing

    def generate_recommendations(self, user_skills: Set[str], vacancy_skills: List[str]) -> List[dict]:
        """Генерирует рекомендации по недостающим навыкам"""
        missing = self.get_missing_skills(user_skills, vacancy_skills)
        recommendations = []

        skill_count = {}

        for vacancy_data in self.prepared_vacancies:
            for skill in vacancy_data['skills']:
                skill_count[skill] = skill_count.get(skill, 0) + 1

        for skill in missing:
            count = skill_count.get(skill, 0)

            if count > 0:
                description = f'Навык "{skill}" встречается в {count} вакансиях. Рекомендуем изучить.'
            else:
                description = f'Рекомендуем изучить навык "{skill}".'

            recommendations.append({
                'skill': skill,
                'description': description,
                'vacancies_count': count
            })

        return recommendations

    def generate_recommendations_from_vacancies(self, user_skills: Set[str], vacancy_skills: List[str],
                                                all_vacancies: List) -> List[dict]:
        """Генерирует рекомендации на основе переданных вакансий"""
        missing = self.get_missing_skills(user_skills, vacancy_skills)
        recommendations = []

        skill_count = {}
        for vacancy in all_vacancies:
            for vs in vacancy.skills:
                skill_name = vs.skill.name
                skill_count[skill_name] = skill_count.get(skill_name, 0) + 1

        for skill in missing:
            count = skill_count.get(skill, 0)

            if count > 0:
                description = f'Навык "{skill}" встречается в {count} вакансиях.'

            recommendations.append({
                'skill': skill,
                'description': description,
                'vacancies_count': count
            })

        return recommendations