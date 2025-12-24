-- ============================================
-- TELEGRAM BOT - SUPABASE SCHEMA v2.0
-- ============================================
-- ВАЖНО: Выполнять по частям если будут ошибки
-- Часть 1: Таблицы и индексы
-- Часть 2: Views и функции (после создания таблиц)
-- ============================================

-- ============================================
-- ЧАСТЬ 1: ТАБЛИЦЫ
-- ============================================

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username TEXT,
    full_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'banned')),
    experience_text TEXT,
    source_text TEXT,
    wallet_address TEXT,
    mentor_id INTEGER,
    referrer_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    referral_earnings DECIMAL(12,2) DEFAULT 0,
    last_activity TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Сервисы
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    icon TEXT DEFAULT '🔹',
    description TEXT,
    manual_link TEXT,
    bot_link TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Профиты
CREATE TABLE IF NOT EXISTS profits (
    id SERIAL PRIMARY KEY,
    worker_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    net_profit DECIMAL(12,2) NOT NULL,
    service_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'hold'
        CHECK (status IN ('hold', 'paid')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

-- Ресурсы
CREATE TABLE IF NOT EXISTS resources (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content_link TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('community', 'resource')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Наставники
CREATE TABLE IF NOT EXISTS mentors (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_name TEXT NOT NULL,
    percent INTEGER NOT NULL CHECK (percent >= 1 AND percent <= 50),
    rating DECIMAL(5,2) DEFAULT 0,
    students_count INTEGER DEFAULT 0,
    total_earned DECIMAL(12,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, service_name)
);

-- Логи админов
CREATE TABLE IF NOT EXISTS admin_logs (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    admin_username TEXT,
    action_type TEXT NOT NULL,
    action_details TEXT,
    target_user_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- История рангов
CREATE TABLE IF NOT EXISTS rank_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_rank TEXT NOT NULL,
    new_rank TEXT NOT NULL,
    old_level INTEGER NOT NULL,
    new_level INTEGER NOT NULL,
    total_profit DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Уведомления
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Настройки бота
CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

-- Настройки прямых платежей
CREATE TABLE IF NOT EXISTS direct_payment_settings (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    requisites TEXT NOT NULL,
    additional_info TEXT,
    support_username TEXT NOT NULL
);

-- Реферальные профиты (история начислений рефереру)
CREATE TABLE IF NOT EXISTS referral_profits (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referral_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profit_id INTEGER NOT NULL REFERENCES profits(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'hold'
        CHECK (status IN ('hold', 'paid')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

-- Профиты наставников (история начислений наставнику)
CREATE TABLE IF NOT EXISTS mentor_profits (
    id SERIAL PRIMARY KEY,
    mentor_id INTEGER NOT NULL REFERENCES mentors(id) ON DELETE CASCADE,
    mentor_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profit_id INTEGER NOT NULL REFERENCES profits(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    percent INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'hold'
        CHECK (status IN ('hold', 'paid')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

-- ============================================
-- ИНДЕКСЫ
-- ============================================

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_profits_worker ON profits(worker_id);
CREATE INDEX IF NOT EXISTS idx_profits_status ON profits(status);
CREATE INDEX IF NOT EXISTS idx_profits_created ON profits(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mentors_active ON mentors(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_referral_profits_referrer ON referral_profits(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_profits_status ON referral_profits(status);
CREATE INDEX IF NOT EXISTS idx_mentor_profits_mentor ON mentor_profits(mentor_user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_profits_status ON mentor_profits(status);

-- ============================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- ============================================

INSERT INTO bot_settings (key, value, description) VALUES
    ('maintenance_mode', 'false', 'Режим обслуживания'),
    ('welcome_message', 'Добро пожаловать!', 'Приветствие'),
    ('min_payout', '50', 'Мин. выплата USD')
ON CONFLICT (key) DO NOTHING;

INSERT INTO direct_payment_settings (id, requisites, additional_info, support_username) VALUES
    (1, 'Не настроено', 'Обратитесь к админу', 'support')
ON CONFLICT (id) DO NOTHING;
