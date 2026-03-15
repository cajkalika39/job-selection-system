from matcher import SkillMatcher


def test_matcher():
    """Функция для тестирования matcher без запуска всего приложения"""
    matcher = SkillMatcher()

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ МОДУЛЯ СРАВНЕНИЯ НАВЫКОВ")
    print("=" * 60)

    # Тест 1: Нормализация навыков
    print("\n1. ТЕСТ НОРМАЛИЗАЦИИ:")
    test_skills = ["Python", "  SQL  ", "Flask!", "React.js", "C++", "Docker?"]
    for skill in test_skills:
        normalized = matcher.normalize_skill(skill)
        print(f"  '{skill}' -> '{normalized}'")

    # Тест 2: Проверка похожести навыков
    print("\n2. ТЕСТ ПОХОЖЕСТИ НАВЫКОВ:")
    test_pairs = [
        ("Python", "python"),
        ("Python", "питон"),
        ("JS", "JavaScript"),
        ("React", "React.js"),
        ("NodeJS", "Node.js"),
        ("SQL", "MySQL"),
        ("Docker", "докер"),
        ("Python", "Java")  # Должно быть False
    ]

    for skill1, skill2 in test_pairs:
        similar = matcher.skills_are_similar(skill1, skill2)
        print(f"  '{skill1}' vs '{skill2}': {'✅ Похожи' if similar else '❌ Не похожи'}")

    # Тест 3: Парсинг строки с навыками
    print("\n3. ТЕСТ ПАРСИНГА:")
    test_strings = [
        "Python, SQL, Flask",
        "Python; SQL; Flask",
        "Python SQL Flask",
        "Python,SQL,Flask",
        "Python, SQL, JavaScript, React"
    ]

    for test_str in test_strings:
        skills = matcher.parse_user_skills(test_str)
        print(f"  '{test_str}' -> {skills}")

    # Тест 4: Расчет процента совпадения
    print("\n4. ТЕСТ РАСЧЕТА ПРОЦЕНТА:")

    # Создаем заглушки навыков для теста
    class MockSkill:
        def __init__(self, name):
            self.name = name

    user_skills = {"python", "flask", "sql", "git"}
    vacancy_skills = [
        MockSkill("Python"),
        MockSkill("Django"),
        MockSkill("SQL"),
        MockSkill("Docker"),
        MockSkill("Git")
    ]

    percentage = matcher.calculate_match_percentage(user_skills, vacancy_skills)
    missing = matcher.get_missing_skills(user_skills, vacancy_skills)

    print(f"  Навыки пользователя: {user_skills}")
    print(f"  Требуемые навыки: {[s.name for s in vacancy_skills]}")
    print(f"  Процент совпадения: {percentage}%")
    print(f"  Недостающие навыки: {missing}")

    # Тест 5: Генерация рекомендаций
    print("\n5. ТЕСТ РЕКОМЕНДАЦИЙ:")
    missing_skills = ["Django", "Docker", "React"]
    recommendations = matcher.get_recommendations(missing_skills)

    for rec in recommendations:
        print(f"\n  📚 {rec['skill']}:")
        print(f"     {rec['description']}")
        print(f"     Ресурсы: {', '.join(rec['resources'])}")


if __name__ == "__main__":
    test_matcher()