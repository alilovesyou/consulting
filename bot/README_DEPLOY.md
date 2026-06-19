# Visa Consulting Telegram Bot — Deploy Guide

Bu document projectni boshqa kompyuterda yoki Ubuntu serverda ishga tushirish uchun yozilgan.

Hozircha deploy qilinadigan qism:

```text
✅ Telegram bot
✅ PostgreSQL database
✅ Local media storage
⏸ Frontend Mini App hozircha deploy qilinmaydi
```

---

## 1. Serverda kerak bo‘ladigan narsalar

Ubuntu serverda quyidagilar bo‘lishi kerak:

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  git \
  postgresql \
  postgresql-contrib
```

---

## 2. Projectni serverga clone qilish

```bash
cd /opt

git clone https://github.com/alilovesyou/consulting.git

cd /opt/consulting
```

Agar project private repository bo‘lsa, GitHub token yoki SSH key kerak bo‘ladi.

---

## 3. PostgreSQL database yaratish

PostgreSQL ichiga kiring:

```bash
sudo -u postgres psql
```

Database va user yarating:

```sql
CREATE DATABASE visabot_db;

CREATE USER visabot_user WITH PASSWORD 'CHANGE_THIS_STRONG_PASSWORD';

GRANT ALL PRIVILEGES ON DATABASE visabot_db TO visabot_user;

\q
```

Keyin schema permission bering:

```bash
sudo -u postgres psql -d visabot_db
```

```sql
GRANT ALL ON SCHEMA public TO visabot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO visabot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO visabot_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO visabot_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO visabot_user;

\q
```

---

## 4. Full SQL setup

`setup.sql` file yarating:

```bash
nano /opt/consulting/setup.sql
```

Ichiga quyidagini to‘liq paste qiling.

Muhim: `1092121944` joyiga asosiy Superadmin Telegram ID yoziladi. `.env` ichidagi `ADMIN_ID` ham shu ID bilan bir xil bo‘lishi kerak.

```sql
-- ==========================================
-- VISA CONSULTING BOT DATABASE
-- FULL FRESH POSTGRESQL SETUP
-- ==========================================

-- Agar database ichini butunlay tozalamoqchi bo'lsangiz,
-- quyidagi 4 qatorni commentdan ochib ishlating.
-- EHTIYOT: hamma table va data o'chadi.

-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;
-- GRANT ALL ON SCHEMA public TO postgres;
-- GRANT ALL ON SCHEMA public TO public;


-- ==========================================
-- 1. USERS
-- user, student, teacher, pending_teacher,
-- rejected_teacher, admin, superadmin
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    full_name VARCHAR(150),
    phone VARCHAR(30),
    region VARCHAR(150),
    age INT,
    role VARCHAR(30) DEFAULT 'user',
    teach_lang VARCHAR(100),
    experience TEXT,
    interface_lang VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- 2. GROUPS
-- ==========================================

CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    language VARCHAR(100) NOT NULL,
    teacher_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    max_capacity INT DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    telegram_link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- 3. GROUP STUDENTS
-- ==========================================

CREATE TABLE IF NOT EXISTS group_students (
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    group_id INT REFERENCES groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, group_id)
);


-- ==========================================
-- 4. PAYMENTS
-- ==========================================

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    language VARCHAR(100),
    course_info TEXT,
    payment_method VARCHAR(30),
    receipt_path VARCHAR(255),
    status VARCHAR(30) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- 5. LESSONS
-- ==========================================

CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY,
    group_id INT REFERENCES groups(id) ON DELETE CASCADE,
    title VARCHAR(255),
    video_path VARCHAR(255),
    material_type VARCHAR(30),
    original_filename VARCHAR(255),
    file_size BIGINT,
    test_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- 6. STUDENT RESULTS
-- ==========================================

CREATE TABLE IF NOT EXISTS student_results (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    group_id INT REFERENCES groups(id) ON DELETE CASCADE,
    teacher_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    result_title VARCHAR(150),
    score VARCHAR(50),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- 7. KICK REQUESTS
-- ==========================================

CREATE TABLE IF NOT EXISTS kick_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    group_id INT REFERENCES groups(id) ON DELETE CASCADE,
    teacher_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    reason TEXT,
    status VARCHAR(30) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- 8. ADMIN ACTIONS
-- ==========================================

CREATE TABLE IF NOT EXISTS admin_actions (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id BIGINT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- 9. INDEXES
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_users_role
ON users(role);

CREATE INDEX IF NOT EXISTS idx_users_interface_lang
ON users(interface_lang);

CREATE INDEX IF NOT EXISTS idx_groups_teacher_id
ON groups(teacher_id);

CREATE INDEX IF NOT EXISTS idx_groups_is_active
ON groups(is_active);

CREATE INDEX IF NOT EXISTS idx_group_students_user_id
ON group_students(user_id);

CREATE INDEX IF NOT EXISTS idx_group_students_group_id
ON group_students(group_id);

CREATE INDEX IF NOT EXISTS idx_payments_user_id
ON payments(user_id);

CREATE INDEX IF NOT EXISTS idx_payments_status
ON payments(status);

CREATE INDEX IF NOT EXISTS idx_lessons_group_id
ON lessons(group_id);

CREATE INDEX IF NOT EXISTS idx_student_results_user_id
ON student_results(user_id);

CREATE INDEX IF NOT EXISTS idx_student_results_teacher_id
ON student_results(teacher_id);

CREATE INDEX IF NOT EXISTS idx_student_results_group_id
ON student_results(group_id);

CREATE INDEX IF NOT EXISTS idx_kick_requests_status
ON kick_requests(status);

CREATE INDEX IF NOT EXISTS idx_kick_requests_teacher_id
ON kick_requests(teacher_id);

CREATE INDEX IF NOT EXISTS idx_kick_requests_user_id
ON kick_requests(user_id);

CREATE INDEX IF NOT EXISTS idx_admin_actions_admin_id
ON admin_actions(admin_id);

CREATE INDEX IF NOT EXISTS idx_admin_actions_action
ON admin_actions(action);

CREATE INDEX IF NOT EXISTS idx_admin_actions_created_at
ON admin_actions(created_at);


-- ==========================================
-- 10. MAIN SUPERADMIN
-- .env ichidagi ADMIN_ID bilan bir xil bo'lishi kerak.
-- ==========================================

INSERT INTO users (
    telegram_id,
    full_name,
    role,
    interface_lang
)
VALUES (
    1092121944,
    'Main Superadmin',
    'superadmin',
    'uz'
)
ON CONFLICT (telegram_id)
DO UPDATE SET
    role = 'superadmin',
    interface_lang = COALESCE(users.interface_lang, EXCLUDED.interface_lang),
    full_name = COALESCE(users.full_name, EXCLUDED.full_name);


-- ==========================================
-- 11. OPTIONAL TEST DATA
-- Kerak bo'lsa commentdan ochib ishlatasiz.
-- ==========================================

-- Test teacher:
-- INSERT INTO users (
--     telegram_id,
--     full_name,
--     phone,
--     region,
--     age,
--     role,
--     teach_lang,
--     experience,
--     interface_lang
-- )
-- VALUES (
--     1111111111,
--     'Test Teacher',
--     '+998900000000',
--     'Sirdaryo, Guliston sh.',
--     30,
--     'teacher',
--     '🇬🇧 Ingliz tili',
--     'Test tajriba',
--     'uz'
-- )
-- ON CONFLICT (telegram_id)
-- DO UPDATE SET
--     role = 'teacher',
--     teach_lang = '🇬🇧 Ingliz tili';


-- Test student:
-- INSERT INTO users (
--     telegram_id,
--     full_name,
--     phone,
--     region,
--     age,
--     role,
--     interface_lang
-- )
-- VALUES (
--     2222222222,
--     'Test Student',
--     '+998901111111',
--     'Sirdaryo, Guliston sh.',
--     22,
--     'student',
--     'uz'
-- )
-- ON CONFLICT (telegram_id)
-- DO UPDATE SET
--     role = 'student';


-- Test group:
-- INSERT INTO groups (
--     name,
--     language,
--     teacher_id,
--     max_capacity,
--     is_active,
--     telegram_link
-- )
-- VALUES (
--     'Ingliz tili - 1-guruh',
--     '🇬🇧 Ingliz tili',
--     1111111111,
--     10,
--     TRUE,
--     'https://t.me/+YourGroupLink'
-- );


-- Test studentni groupga qo'shish:
-- INSERT INTO group_students (
--     user_id,
--     group_id
-- )
-- VALUES (
--     2222222222,
--     1
-- )
-- ON CONFLICT (user_id, group_id)
-- DO NOTHING;


-- Test result:
-- INSERT INTO student_results (
--     user_id,
--     group_id,
--     teacher_id,
--     result_title,
--     score,
--     comment
-- )
-- VALUES (
--     2222222222,
--     1,
--     1111111111,
--     '1-test',
--     '85/100',
--     'Yaxshi natija'
-- );


-- ==========================================
-- 12. FINAL CHECK
-- ==========================================

SELECT 'Database setup completed successfully!' AS status;
```

SQL setup’ni run qiling:

```bash
sudo -u postgres psql -d visabot_db -f /opt/consulting/setup.sql
```

Yana permission bering:

```bash
sudo -u postgres psql -d visabot_db
```

```sql
GRANT ALL ON SCHEMA public TO visabot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO visabot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO visabot_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO visabot_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO visabot_user;

\q
```

---

## 5. Bot .env file yaratish

```bash
cd /opt/consulting/bot

nano .env
```

Ichiga quyidagini yozing:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

DB_USER=visabot_user
DB_PASSWORD=CHANGE_THIS_STRONG_PASSWORD
DB_HOST=localhost
DB_PORT=5432
DB_NAME=visabot_db

ADMIN_ID=1092121944

API_HOST=127.0.0.1
API_PORT=8000

MINI_APP_URL=
```

Hozir frontend ishlatilmayotgani uchun `MINI_APP_URL` bo‘sh turishi mumkin.

Muhim:

```text
ADMIN_ID = asosiy Superadmin Telegram ID
```

SQL ichidagi superadmin ID bilan `.env` ichidagi `ADMIN_ID` bir xil bo‘lishi kerak.

---

## 6. Python virtual environment yaratish

```bash
cd /opt/consulting/bot

python3 -m venv venv

source venv/bin/activate

pip install --upgrade pip

pip install -r requirements.txt
```

Agar `requirements.txt` ichida FastAPI yoki Uvicorn yo‘q bo‘lsa, lekin project import qilsa, qo‘shing:

```bash
pip install fastapi uvicorn
```

---

## 7. Media papkalarni tayyorlash

Bot receipt va lesson fayllarni local storage’da saqlaydi.

```bash
mkdir -p /opt/consulting/bot/media/receipts
mkdir -p /opt/consulting/bot/media/lessons

chmod -R 755 /opt/consulting/bot/media
```

---

## 8. Botni manual test qilish

```bash
cd /opt/consulting/bot

source venv/bin/activate

python main.py
```

Agar hammasi to‘g‘ri bo‘lsa, terminalda shunga o‘xshash chiqadi:

```text
PostgreSQL bazasiga muvaffaqiyatli ulandi!
Bot ishga tushdi...
Start polling
```

Telegramda botga kiring:

```text
/start
```

Tekshiriladigan flow:

```text
1. /start
2. Til tanlash
3. Superadmin panel chiqishi
4. Admin qo‘shish
5. O‘quvchi ro‘yxatdan o‘tishi
6. Kurs tanlash
7. Chek yuborish
8. Admin approve qilish
9. Teacher ariza yuborish
10. Teacher approve qilish
11. Guruh yaratish
12. Dars yuklash
```

Test tugagach terminalda:

```bash
CTRL + C
```

---

## 9. systemd service yaratish

Botni 24/7 ishlatish uchun systemd service yaratiladi.

```bash
nano /etc/systemd/system/visabot.service
```

Ichiga yozing:

```ini
[Unit]
Description=Visa Consulting Telegram Bot
After=network.target postgresql.service

[Service]
WorkingDirectory=/opt/consulting/bot
ExecStart=/opt/consulting/bot/venv/bin/python /opt/consulting/bot/main.py
Restart=always
RestartSec=5
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Service’ni yoqing:

```bash
systemctl daemon-reload

systemctl enable visabot

systemctl start visabot

systemctl status visabot
```

Loglarni ko‘rish:

```bash
journalctl -u visabot -f
```

Service’ni restart qilish:

```bash
systemctl restart visabot
```

Service’ni to‘xtatish:

```bash
systemctl stop visabot
```

---

## 10. Serverda project update qilish

Agar localda code o‘zgarsa va GitHub’ga push qilinsa, serverda update qilish:

```bash
cd /opt/consulting

git pull origin main
```

Keyin dependencies o‘zgargan bo‘lsa:

```bash
cd /opt/consulting/bot

source venv/bin/activate

pip install -r requirements.txt
```

Botni restart qiling:

```bash
systemctl restart visabot

journalctl -u visabot -f
```

---

## 11. Database’ni fresh tozalash

Agar database’ni butunlay tozalab fresh qilish kerak bo‘lsa:

```bash
sudo -u postgres psql -d visabot_db
```

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
GRANT ALL ON SCHEMA public TO visabot_user;

\q
```

Keyin full setup qayta run qilinadi:

```bash
sudo -u postgres psql -d visabot_db -f /opt/consulting/setup.sql
```

Permission qayta bering:

```bash
sudo -u postgres psql -d visabot_db
```

```sql
GRANT ALL ON SCHEMA public TO visabot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO visabot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO visabot_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO visabot_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO visabot_user;

\q
```

Botni restart qiling:

```bash
systemctl restart visabot
```

---

## 12. Backup qilish

Muhim backup qilinadigan joylar:

```text
1. PostgreSQL database
2. bot/media/lessons
3. bot/media/receipts
4. bot/.env
```

Database backup:

```bash
sudo -u postgres pg_dump visabot_db > /opt/visabot_db_backup.sql
```

Media backup:

```bash
tar -czvf /opt/visabot_media_backup.tar.gz /opt/consulting/bot/media
```

Restore database:

```bash
sudo -u postgres psql -d visabot_db < /opt/visabot_db_backup.sql
```

Restore media:

```bash
tar -xzvf /opt/visabot_media_backup.tar.gz -C /
```

---

## 13. Gitignore tekshiruv

Repository ichida `.env`, real receipt/video/pdf fayllar va virtual environment push qilinmasligi kerak.

`.gitignore` ichida quyidagilar bo‘lishi kerak:

```gitignore
bot/.env
bot/venv/
bot/__pycache__/
**/__pycache__/
*.py[cod]

bot/media/*
!bot/media/.gitkeep
!bot/media/lessons/
!bot/media/lessons/.gitkeep
!bot/media/receipts/
!bot/media/receipts/.gitkeep

frontend-miniapp/.env
frontend-miniapp/node_modules/
frontend-miniapp/dist/

.vscode/
```

Git status tekshirish:

```bash
git status --ignored
```

`.env` yoki `media/receipts/*.jpg` staged bo‘lib qolmasligi kerak.

---

## 14. Hozircha frontend deploy qilinmaydi

Frontend Mini App hozircha to‘xtab turadi.

Shuning uchun hozir kerak emas:

```text
Nginx
HTTPS domain
Vercel
Mini App deploy
API public URL
```

Bot oddiy Telegram polling orqali ishlaydi.

Agar keyin Mini App qo‘shilsa, alohida deploy qilinadi va `.env` ichida:

```env
MINI_APP_URL=https://your-domain.com
```

qilib yoziladi.

---

## 15. Final checklist

Serverga topshirishdan oldin:

```text
✅ git pull qilingan
✅ bot/.env yaratilgan
✅ PostgreSQL database yaratilgan
✅ setup.sql run qilingan
✅ Superadmin ID to‘g‘ri yozilgan
✅ requirements.txt install qilingan
✅ media papkalar yaratilgan
✅ python main.py manual testdan o‘tgan
✅ systemd service ishlayapti
✅ journalctl loglarda error yo‘q
✅ /start Telegramda ishlayapti
```

Agar service status’da `active (running)` chiqsa, bot serverda ishlayapti:

```bash
systemctl status visabot
```
