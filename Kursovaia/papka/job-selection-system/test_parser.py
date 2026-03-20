from hh_parser import HHParser
from app import app
from extensions import db


def test_parser():
    """Тестирование парсера hh.ru"""
    parser = HHParser()

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ПАРСЕРА HH.RU")
    print("=" * 60)

    # Тест 1: Поиск вакансий
    print("\n1. ПОИСК ВАКАНСИЙ:")
    vacancies = parser.search_vacancies("Python", area=113, pages=1)

    print(f"\nНайдено вакансий: {len(vacancies)}")

    if vacancies:
        # Покажем первые 3 вакансии
        for i, vac in enumerate(vacancies[:3], 1):
            print(f"\n--- Вакансия {i} ---")
            print(f"Название: {vac['title']}")
            print(f"Компания: {vac['company']}")
            print(f"Локация: {vac['location']}")
            print(f"Зарплата: {vac['salary_min']} - {vac['salary_max']} {vac['currency']}")
            print(f"Навыки: {', '.join(vac['skills'])}")
            print(f"URL: {vac['url']}")

    # Тест 2: Сохранение в БД
    print("\n2. СОХРАНЕНИЕ В БД:")
    with app.app_context():
        saved = parser.save_vacancies_to_db(vacancies)
        print(f"Сохранено вакансий: {saved}")


if __name__ == "__main__":
    test_parser()