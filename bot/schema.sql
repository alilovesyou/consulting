CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    full_name TEXT,
    phone TEXT,
    region TEXT,
    district TEXT,
    age INTEGER,
    role TEXT NOT NULL DEFAULT 'user',
    teach_lang TEXT,
    experience TEXT,
    interface_lang TEXT NOT NULL DEFAULT 'uz',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    language TEXT,
    teacher_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    max_capacity INTEGER NOT NULL DEFAULT 10,
    current_count INTEGER NOT NULL DEFAULT 0,
    telegram_link TEXT,
    link TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    language TEXT,
    lang_code TEXT,
    package_type TEXT,
    course_info TEXT,
    payment_method TEXT,
    amount NUMERIC(12,2),
    status TEXT NOT NULL DEFAULT 'pending',
    receipt_file_id TEXT,
    receipt_path TEXT,
    receipt_url TEXT,
    group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    approved_by BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    rejected_by BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    reject_reason TEXT,
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_students (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'active',
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(group_id, user_id)
);

CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    video_path TEXT,
    material_type TEXT DEFAULT 'document',
    original_filename TEXT,
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_results (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    teacher_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    result_title TEXT NOT NULL,
    score TEXT,
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kick_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    teacher_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    admin_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    reject_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_actions (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id BIGINT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method);
CREATE INDEX IF NOT EXISTS idx_groups_teacher ON groups(teacher_id);
CREATE INDEX IF NOT EXISTS idx_group_students_user ON group_students(user_id);
CREATE INDEX IF NOT EXISTS idx_lessons_group ON lessons(group_id);
CREATE INDEX IF NOT EXISTS idx_results_user ON student_results(user_id);
CREATE INDEX IF NOT EXISTS idx_results_teacher ON student_results(teacher_id);
CREATE INDEX IF NOT EXISTS idx_kick_status ON kick_requests(status);

INSERT INTO users (telegram_id, full_name, role, interface_lang)
VALUES (1092121944, 'Main Superadmin', 'superadmin', 'uz')
ON CONFLICT (telegram_id) DO UPDATE
SET role = 'superadmin',
    full_name = COALESCE(users.full_name, EXCLUDED.full_name),
    interface_lang = COALESCE(users.interface_lang, EXCLUDED.interface_lang);
