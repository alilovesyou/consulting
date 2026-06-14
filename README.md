# consulting
python 3.12.3

Postgresql database: 

visabot_db 
password 2102

-- Foydalanuvchilar jadvali (User, Teacher, Admin, Superadmin)
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY, -- Telegram ID har doim BIGINT bo'lishi kerak
    full_name VARCHAR(100),
    phone VARCHAR(20),
    region VARCHAR(50),
    age INT,
    role VARCHAR(20) DEFAULT 'user', -- user, teacher, admin, superadmin
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guruhlar jadvali
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    language VARCHAR(50) NOT NULL,
    teacher_id BIGINT REFERENCES users(telegram_id),
    max_capacity INT DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    telegram_link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- To'lovlar jadvali
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id),
    language VARCHAR(50),
    payment_method VARCHAR(20), -- cash yoki card
    receipt_path VARCHAR(255), -- Rasmni lokal kompyuterdagi manzili
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Darslar va materiallar jadvali (Mini App uchun)
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    group_id INT REFERENCES groups(id),
    title VARCHAR(200),
    video_path VARCHAR(255),
    test_data JSONB, -- Test savollari va javoblari JSON formatida saqlanadi
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


empty group yaratish: 

INSERT INTO groups (name, language, is_active, telegram_link) 
VALUES ('Ingliz tili - 1-guruh', 'Ingliz tili', TRUE, 'https://t.me/+AbCdEfGhIjKlMnOp');

