-- Создание базы данных
CREATE DATABASE IF NOT EXISTS job_matching_system;
USE job_matching_system;

-- Таблица пользователей
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Таблица навыков (справочник всех возможных навыков)
CREATE TABLE skills (
    id INT PRIMARY KEY AUTO_INCREMENT,
    skill_name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица вакансий
CREATE TABLE jobs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    company_name VARCHAR(100) NOT NULL,
    description TEXT,
    salary_min DECIMAL(10, 2),
    salary_max DECIMAL(10, 2),
    location VARCHAR(100),
    employment_type ENUM('full-time', 'part-time', 'contract', 'internship') DEFAULT 'full-time',
    experience_required INT, -- в годах
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Таблица связей вакансий с требуемыми навыками
CREATE TABLE job_skills (
    id INT PRIMARY KEY AUTO_INCREMENT,
    job_id INT NOT NULL,
    skill_id INT NOT NULL,
    importance_level ENUM('mandatory', 'preferred', 'bonus') DEFAULT 'mandatory',
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    UNIQUE KEY unique_job_skill (job_id, skill_id)
);

-- Таблица навыков пользователей
CREATE TABLE user_skills (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    proficiency_level ENUM('beginner', 'intermediate', 'advanced', 'expert') DEFAULT 'intermediate',
    years_experience INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_skill (user_id, skill_id)
);

-- Таблица резюме пользователей
CREATE TABLE resumes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    file_path VARCHAR(255),
    file_name VARCHAR(255),
    parsed_text TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица результатов сопоставления вакансий
CREATE TABLE job_matches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    job_id INT NOT NULL,
    match_percentage DECIMAL(5, 2),
    missing_skills TEXT, -- JSON формат или текст с перечислением
    recommendations TEXT, -- JSON формат или текст с рекомендациями
    viewed BOOLEAN DEFAULT FALSE,
    saved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_job_match (user_id, job_id)
);

-- Таблица для хранения аналитики по навыкам
CREATE TABLE skills_analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    skill_id INT NOT NULL,
    total_jobs_requiring INT DEFAULT 0,
    avg_salary_with_skill DECIMAL(10, 2),
    demand_trend ENUM('rising', 'stable', 'declining') DEFAULT 'stable',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Таблица для истории поиска пользователей
CREATE TABLE search_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    search_query VARCHAR(255),
    filters_applied TEXT,
    results_count INT,
    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Индексы для оптимизации поиска
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_company ON jobs(company_name);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_is_active ON jobs(is_active);
CREATE INDEX idx_user_skills_user ON user_skills(user_id);
CREATE INDEX idx_job_skills_job ON job_skills(job_id);
CREATE INDEX idx_job_skills_skill ON job_skills(skill_id);
CREATE INDEX idx_job_matches_user ON job_matches(user_id);
CREATE INDEX idx_job_matches_percentage ON job_matches(match_percentage);

-- Представление для удобного просмотра вакансий с навыками
CREATE VIEW vw_jobs_with_skills AS
SELECT 
    j.id,
    j.title,
    j.company_name,
    j.location,
    j.salary_min,
    j.salary_max,
    j.employment_type,
    GROUP_CONCAT(DISTINCT s.skill_name ORDER BY 
        CASE js.importance_level 
            WHEN 'mandatory' THEN 1 
            WHEN 'preferred' THEN 2 
            ELSE 3 
        END
    ) as required_skills
FROM jobs j
LEFT JOIN job_skills js ON j.id = js.job_id
LEFT JOIN skills s ON js.skill_id = s.id
WHERE j.is_active = TRUE
GROUP BY j.id;

-- Представление для анализа пользовательских навыков
CREATE VIEW vw_user_skills_analysis AS
SELECT 
    u.id as user_id,
    u.username,
    u.full_name,
    COUNT(DISTINCT us.skill_id) as total_skills,
    GROUP_CONCAT(DISTINCT s.skill_name) as skills_list,
    (
        SELECT COUNT(DISTINCT j.id) 
        FROM jobs j
        JOIN job_skills js ON j.id = js.job_id
        WHERE js.skill_id IN (SELECT skill_id FROM user_skills WHERE user_id = u.id)
        AND j.is_active = TRUE
    ) as potential_jobs_count
FROM users u
LEFT JOIN user_skills us ON u.id = us.user_id
LEFT JOIN skills s ON us.skill_id = s.id
GROUP BY u.id;

-- Представление для топ-вакансий по совпадению навыков
CREATE VIEW vw_top_matches AS
SELECT 
    jm.*,
    j.title as job_title,
    j.company_name,
    u.username,
    u.full_name
FROM job_matches jm
JOIN jobs j ON jm.job_id = j.id
JOIN users u ON jm.user_id = u.id
WHERE jm.match_percentage >= 70
ORDER BY jm.match_percentage DESC;

-- Процедура для расчета процента совпадения навыков
DELIMITER //

CREATE PROCEDURE CalculateJobMatch(
    IN p_user_id INT,
    IN p_job_id INT
)
BEGIN
    DECLARE total_required_skills INT;
    DECLARE matched_skills INT;
    DECLARE match_percentage DECIMAL(5, 2);
    DECLARE missing_skills_text TEXT;
    
    -- Подсчет общего количества требуемых навыков
    SELECT COUNT(*) INTO total_required_skills
    FROM job_skills
    WHERE job_id = p_job_id;
    
    -- Подсчет совпадающих навыков
    SELECT COUNT(*) INTO matched_skills
    FROM job_skills js
    INNER JOIN user_skills us ON js.skill_id = us.skill_id
    WHERE js.job_id = p_job_id AND us.user_id = p_user_id;
    
    -- Расчет процента совпадения
    IF total_required_skills > 0 THEN
        SET match_percentage = (matched_skills / total_required_skills) * 100;
    ELSE
        SET match_percentage = 0;
    END IF;
    
    -- Получение недостающих навыков
    SELECT GROUP_CONCAT(s.skill_name) INTO missing_skills_text
    FROM job_skills js
    INNER JOIN skills s ON js.skill_id = s.id
    LEFT JOIN user_skills us ON js.skill_id = us.skill_id AND us.user_id = p_user_id
    WHERE js.job_id = p_job_id AND us.skill_id IS NULL;
    
    -- Сохранение результата
    INSERT INTO job_matches (user_id, job_id, match_percentage, missing_skills)
    VALUES (p_user_id, p_job_id, match_percentage, missing_skills_text)
    ON DUPLICATE KEY UPDATE
        match_percentage = VALUES(match_percentage),
        missing_skills = VALUES(missing_skills),
        created_at = CURRENT_TIMESTAMP;
    
END//

-- Триггер для обновления аналитики навыков
CREATE TRIGGER update_skills_analytics
AFTER INSERT ON job_skills
FOR EACH ROW
BEGIN
    INSERT INTO skills_analytics (skill_id, total_jobs_requiring)
    VALUES (NEW.skill_id, 1)
    ON DUPLICATE KEY UPDATE
        total_jobs_requiring = total_jobs_requiring + 1;
END//

DELIMITER ;

-- Вставка начальных данных (примеры навыков)
INSERT INTO skills (skill_name, category) VALUES
('Python', 'Programming'),
('JavaScript', 'Programming'),
('Java', 'Programming'),
('SQL', 'Database'),
('Flask', 'Web Framework'),
('Django', 'Web Framework'),
('React', 'Frontend'),
('Angular', 'Frontend'),
('MySQL', 'Database'),
('PostgreSQL', 'Database'),
('Git', 'DevTools'),
('Docker', 'DevOps'),
('Kubernetes', 'DevOps'),
('AWS', 'Cloud'),
('Project Management', 'Management'),
('Agile', 'Methodology'),
('Communication', 'Soft Skills'),
('Team Leadership', 'Soft Skills'),
('Machine Learning', 'Data Science'),
('Data Analysis', 'Data Science');

-- Вставка примера вакансии
INSERT INTO jobs (title, company_name, description, salary_min, salary_max, location, employment_type, experience_required) VALUES
('Python Developer', 'Tech Corp', 'Разработка веб-приложений на Python', 150000, 250000, 'Москва', 'full-time', 3);

-- Добавление навыков для примера вакансии
INSERT INTO job_skills (job_id, skill_id, importance_level) VALUES
(1, 1, 'mandatory'),  -- Python
(1, 2, 'preferred'),  -- JavaScript
(1, 4, 'mandatory'),  -- SQL
(1, 5, 'preferred'),  -- Flask
(1, 9, 'mandatory');  -- MySQL

-- Создание пользователя с правами (для Flask приложения)
CREATE USER IF NOT EXISTS 'job_app'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON job_matching_system.* TO 'job_app'@'localhost';
FLUSH PRIVILEGES;