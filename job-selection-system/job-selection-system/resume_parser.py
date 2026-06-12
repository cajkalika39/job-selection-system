import re
import PyPDF2
import docx
from pathlib import Path
from typing import Set, List


class ResumeParser:
    """Парсер резюме для извлечения навыков"""
    SKILLS_DB = {
        'python': ['python', 'django', 'flask', 'fastapi', 'numpy', 'pandas', 'scikit-learn'],
        'javascript': ['javascript', 'js', 'node.js', 'nodejs', 'react', 'vue', 'angular', 'typescript'],
        'java': ['java', 'spring', 'hibernate', 'maven', 'gradle'],
        'c++': ['c++', 'cpp', 'cplusplus', 'qt', 'boost'],
        'c#': ['c#', 'csharp', '.net', 'asp.net', 'unity'],
        'php': ['php', 'laravel', 'symfony', 'wordpress', 'yii'],
        'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'mongodb', 'redis'],
        'git': ['git', 'github', 'gitlab', 'bitbucket'],
        'docker': ['docker', 'container', 'kubernetes', 'k8s', 'swarm'],
        'linux': ['linux', 'unix', 'bash', 'shell', 'ubuntu', 'centos'],
        'html': ['html', 'html5', 'css', 'css3', 'sass', 'less', 'bootstrap'],
        'testing': ['testing', 'pytest', 'unittest', 'junit', 'selenium', 'qa'],
        'rest api': ['rest', 'api', 'restful', 'soap', 'graphql'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud', 'google cloud', 'amazon web services'],
        'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence', 'deep learning', 'nlp'],
        'data analysis': ['data analysis', 'data science', 'analytics', 'power bi', 'tableau'],
        'project management': ['project management', 'agile', 'scrum', 'kanban', 'jira', 'trello'],
        'english': ['english', 'английский', 'ielts', 'toefl'],
        'communication': ['communication', 'teamwork', 'collaboration', 'soft skills'],
    }

    @staticmethod
    def extract_text_from_pdf(file_path: Path) -> str:
        """Извлекает текст из PDF файла"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Ошибка при чтении PDF: {str(e)}")
        return text

    @staticmethod
    def extract_text_from_docx(file_path: Path) -> str:
        """Извлекает текст из DOCX файла"""
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"
        except Exception as e:
            raise Exception(f"Ошибка при чтении DOCX: {str(e)}")
        return text

    @classmethod
    def parse_resume(cls, file_path: Path) -> dict:
        """Основной метод для парсинга резюме"""
        file_extension = file_path.suffix.lower()

        if file_extension == '.pdf':
            text = cls.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            text = cls.extract_text_from_docx(file_path)
        else:
            raise Exception(f"Неподдерживаемый формат файла: {file_extension}. Поддерживаются: .pdf, .docx")

        if not text.strip():
            raise Exception(
                "Не удалось извлечь текст из файла. Возможно, файл защищен или содержит только изображения.")

        skills = cls.extract_skills_from_text(text)

        additional_info = cls.extract_additional_info(text)

        return {
            'text': text[:1000],
            'skills': skills,
            'additional_info': additional_info
        }

    @classmethod
    def extract_skills_from_text(cls, text: str) -> Set[str]:
        """Извлекает навыки из текста"""
        text_lower = text.lower()
        found_skills = set()

        for main_skill, variations in cls.SKILLS_DB.items():
            for variation in variations:
                pattern = r'\b' + re.escape(variation) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.add(main_skill.capitalize())
                    break

        quoted_skills = re.findall(r'"([^"]+)"', text)
        for skill in quoted_skills:
            if len(skill) < 30:
                found_skills.add(skill.strip().capitalize())

        return found_skills

    @classmethod
    def extract_additional_info(cls, text: str) -> dict:
        """Извлекает дополнительную информацию (email, телефон, имя)"""
        info = {
            'email': None,
            'phone': None,
            'name': None
        }

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            info['email'] = emails[0]

        phone_pattern = r'(\+7|8)[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
        phones = re.findall(phone_pattern, text)
        if phones:
            info['phone'] = phones[0]

        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 3 and len(line) < 50 and not any(c.isdigit() for c in line[:3]):
                words = line.split()
                if 2 <= len(words) <= 4:
                    info['name'] = line
                    break

        return info