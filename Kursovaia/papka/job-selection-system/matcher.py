import re
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Set


class SkillMatcher:
    """Класс для сравнения навыков пользователя с требованиями вакансий"""

    def __init__(self):
        # Синонимы навыков для более умного сравнения
        self.skill_synonyms = {
            'python': ['питон', 'пайтон'],
            'js': ['javascript', 'ecmascript'],
            'ts': ['typescript'],
            'react': ['reactjs', 'react.js'],
            'vue': ['vuejs', 'vue.js'],
            'node': ['nodejs', 'node.js', 'node js'],
            'sql': ['mysql', 'postgresql', 'sqlite', 'oracle', 'базы данных'],
            'nosql': ['mongodb', 'redis', 'cassandra'],
            'docker': ['докер', 'container'],
            'kubernetes': ['k8s', 'кубернетес'],
            'git': ['гит', 'github', 'gitlab'],
            'flask': ['фласк'],
            'django': ['джанго'],
            'oop': ['объектно-ориентированное программирование'],
            'rest': ['restful', 'rest api', 'restapi'],
            'api': ['апи'],
            'html': ['htm'],
            'css': ['стили'],
            'aws': ['amazon web services'],
            'linux': ['линукс', 'unix']
        }

    def normalize_skill(self, skill: str) -> str:
        """
        Нормализует название навыка для сравнения

        Args:
            skill: исходное название навыка

        Returns:
            str: нормализованное название
        """
        # Приводим к нижнему регистру и удаляем лишние пробелы
        normalized = skill.lower().strip()

        # Удаляем специальные символы и лишнее
        normalized = re.sub(r'[^\w\s]', '', normalized)

        return normalized

    def skills_are_similar(self, skill1: str, skill2: str, threshold: float = 0.8) -> bool:
        """
        Проверяет, являются ли два навыка похожими

        Args:
            skill1: первый навык
            skill2: второй навык
            threshold: порог схожести (0-1)

        Returns:
            bool: True если навыки похожи
        """
        norm1 = self.normalize_skill(skill1)
        norm2 = self.normalize_skill(skill2)

        # Прямое совпадение
        if norm1 == norm2:
            return True

        # Проверка по синонимам
        for key, synonyms in self.skill_synonyms.items():
            if norm1 in [key] + synonyms and norm2 in [key] + synonyms:
                return True
            if norm2 in [key] + synonyms and norm1 in [key] + synonyms:
                return True

        # Проверка на вхождение одного в другой
        if norm1 in norm2 or norm2 in norm1:
            if len(norm1) > 3 and len(norm2) > 3:  # Чтобы избежать ложных срабатываний на коротких словах
                return True

        # Используем SequenceMatcher для нечеткого сравнения
        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        return similarity >= threshold

    def parse_user_skills(self, skills_input: str) -> Set[str]:
        """
        Парсит строку с навыками пользователя

        Args:
            skills_input: строка с навыками (через запятую, пробелы и т.д.)

        Returns:
            Set[str]: множество нормализованных навыков
        """
        if not skills_input:
            return set()

        # Разделяем по запятым, точкам с запятой или пробелам
        raw_skills = re.split(r'[,;.\s]+', skills_input)

        # Фильтруем пустые строки и нормализуем
        user_skills = set()
        for skill in raw_skills:
            if skill and len(skill) > 1:  # Игнорируем одиночные символы
                normalized = self.normalize_skill(skill)
                if normalized:
                    user_skills.add(normalized)

        return user_skills

    def calculate_match_percentage(self, user_skills: Set[str], vacancy_skills: List) -> float:
        """
        Рассчитывает процент совпадения навыков пользователя с требованиями вакансии

        Args:
            user_skills: множество навыков пользователя (нормализованные)
            vacancy_skills: список навыков, требуемых в вакансии

        Returns:
            float: процент совпадения (0-100)
        """
        if not vacancy_skills:
            return 0.0

        # Извлекаем названия навыков вакансии
        vacancy_skill_names = [skill.name for skill in vacancy_skills]

        # Подсчитываем совпадения
        matched_skills = 0
        for vacancy_skill in vacancy_skill_names:
            normalized_vacancy_skill = self.normalize_skill(vacancy_skill)

            # Проверяем каждый навык пользователя
            for user_skill in user_skills:
                if self.skills_are_similar(user_skill, normalized_vacancy_skill):
                    matched_skills += 1
                    break

        # Рассчитываем процент
        percentage = (matched_skills / len(vacancy_skills)) * 100

        return round(percentage, 2)

    def get_missing_skills(self, user_skills: Set[str], vacancy_skills: List) -> List[str]:
        """
        Определяет недостающие навыки для конкретной вакансии

        Args:
            user_skills: множество навыков пользователя
            vacancy_skills: список навыков, требуемых в вакансии

        Returns:
            List[str]: список недостающих навыков
        """
        missing = []

        for vacancy_skill in vacancy_skills:
            normalized_vacancy = self.normalize_skill(vacancy_skill.name)
            found = False

            for user_skill in user_skills:
                if self.skills_are_similar(user_skill, normalized_vacancy):
                    found = True
                    break

            if not found:
                missing.append(vacancy_skill.name)

        return missing

    def get_recommendations(self, missing_skills: List[str]) -> List[Dict[str, str]]:
        """
        Генерирует рекомендации по изучению недостающих навыков

        Args:
            missing_skills: список недостающих навыков

        Returns:
            List[Dict]: список рекомендаций с названиями и описаниями
        """
        recommendations = []

        # База знаний по навыкам (можно расширить)
        skill_info = {
            'Python': {
                'description': 'Язык программирования, широко используется в веб-разработке, анализе данных, AI',
                'resources': ['Курс на Stepik.org', 'Документация на python.org', 'Книга "Изучаем Python" Марка Лутца']
            },
            'Flask': {
                'description': 'Легковесный веб-фреймворк для Python',
                'resources': ['Официальная документация', 'Курс "Flask для начинающих" на YouTube']
            },
            'Django': {
                'description': 'Мощный веб-фреймворк для Python',
                'resources': ['Django Girls Tutorial', 'Курс на Django Project']
            },
            'SQL': {
                'description': 'Язык запросов к базам данных',
                'resources': ['SQL Academy', 'Курс "SQL для начинающих" на YouTube']
            },
            'Git': {
                'description': 'Система контроля версий',
                'resources': ['Git How To', 'Pro Git книга']
            },
            'Docker': {
                'description': 'Платформа для контейнеризации приложений',
                'resources': ['Docker Get Started', 'Курс на Udemy']
            },
            'JavaScript': {
                'description': 'Язык программирования для веб-разработки',
                'resources': ['JavaScript.info', 'Курс на learn.javascript.ru']
            },
            'React': {
                'description': 'Библиотека для создания пользовательских интерфейсов',
                'resources': ['React Documentation', 'Курс на purpleschool.ru']
            }
        }

        for skill in missing_skills[:5]:  # Ограничиваем 5 рекомендациями
            info = skill_info.get(skill, {
                'description': f'Изучите {skill} для повышения квалификации',
                'resources': [f'Найдите курсы по {skill} на популярных образовательных платформах']
            })

            recommendations.append({
                'skill': skill,
                'description': info['description'],
                'resources': info['resources']
            })

        return recommendations

    def match_vacancies(self, user_skills_input: str, vacancies: List = None) -> List[Dict]:
        """
        Основной метод для подбора вакансий по навыкам пользователя

        Args:
            user_skills_input: строка с навыками пользователя
            vacancies: список вакансий (если None, берет все из БД)

        Returns:
            List[Dict]: список вакансий с процентами совпадения и недостающими навыками
        """
        # Парсим навыки пользователя
        user_skills = self.parse_user_skills(user_skills_input)

        if not user_skills:
            return []

        # Получаем все вакансии, если не переданы
        if vacancies is None:
            from models import Vacancy
            vacancies = Vacancy.query.all()

        results = []

        for vacancy in vacancies:
            # Получаем навыки вакансии
            vacancy_skills = [vs.skill for vs in vacancy.skills]

            # Рассчитываем процент совпадения
            match_percentage = self.calculate_match_percentage(user_skills, vacancy_skills)

            # Получаем недостающие навыки
            missing_skills = self.get_missing_skills(user_skills, vacancy_skills)

            # Генерируем рекомендации
            recommendations = self.get_recommendations(missing_skills)

            results.append({
                'vacancy': vacancy,
                'match_percentage': match_percentage,
                'missing_skills': missing_skills,
                'recommendations': recommendations,
                'required_skills_count': len(vacancy_skills),
                'matched_skills_count': len(vacancy_skills) - len(missing_skills)
            })

        # Сортируем по проценту совпадения (от большего к меньшему)
        results.sort(key=lambda x: x['match_percentage'], reverse=True)

        return results