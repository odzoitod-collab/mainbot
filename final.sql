-- ====================================================================================
-- TELEGRAM BOT - ПОЛНАЯ БАЗА ДАННЫХ (ФИНАЛЬНАЯ ВЕРСИЯ)
-- ====================================================================================
-- Этот файл содержит полную схему базы данных для Telegram бота
-- Включает: очистку, создание таблиц, индексы, функции, views и начальные данные
-- Выполнять целиком или по частям в указанном порядке
-- ====================================================================================

-- ====================================================================================
-- ЧАСТЬ 1: ПОЛНАЯ ОЧИСТКА (Выполнять осторожно, удаляет все данные!)
-- ====================================================================================

-- Удаляем функции
DROP FUNCTION IF EXISTS get_user_stats(BIGINT);
DROP FUNCTION IF EXISTS get_top_workers(TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_user_position(BIGINT);
DROP FUNCTION IF EXISTS get_team_stats();
DROP FUNCTION IF EXISTS get_unpaid_profits_summary();
DROP FUNCTION IF EXISTS get_unpaid_referral_summary();
DROP FUNCTION IF EXISTS get_unpaid_mentor_summary();

-- Удаляем views
DROP VIEW IF EXISTS mentor_details;
DROP VIEW IF EXISTS worker_stats;
DROP VIEW IF EXISTS active_workers_stats;
DROP VIEW IF EXISTS service_stats;

-- Удаляем таблицы (в порядке обратном зависимостям)
DROP TABLE IF EXISTS referral_profits CASCADE;
DROP TABLE IF EXISTS mentor_profits CASCADE;
DROP TABLE IF EXISTS profits CASCADE;
DROP TABLE IF EXISTS mentors CASCADE;
DROP TABLE IF EXISTS resources CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS admin_logs CASCADE;
DROP TABLE IF EXISTS rank_history CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS direct_payment_settings CASCADE;
DROP TABLE IF EXISTS bot_settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Опционально: удаляем таблицы, которые упоминались в DROP, но не были описаны в CREATE
-- (Оставьте закомментированным, если эти таблицы вам нужны для других целей)
-- DROP TABLE IF EXISTS answers CASCADE;
-- DROP TABLE IF EXISTS questions CASCADE;
-- DROP TABLE IF EXISTS user_action_logs CASCADE;

-- Удаляем типы если есть
DROP TYPE IF EXISTS user_status CASCADE;
DROP TYPE IF EXISTS profit_status CASCADE;
DROP TYPE IF EXISTS resource_type CASCADE;
DROP TYPE IF EXISTS admin_action_type CASCADE;
DROP TYPE IF EXISTS notification_type CASCADE;
DROP TYPE IF EXISTS user_action_type CASCADE;

-- ====================================================================================
-- ЧАСТЬ 2: СОЗДАНИЕ ТАБЛИЦ
-- ====================================================================================

-- 1. Пользователи (Базовая таблица)
CREATE TABLE users (
    id BIGINT PRIMARY KEY, -- Telegram ID
    username TEXT,
    full_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'banned')),
    experience_text TEXT,
    source_text TEXT,
    wallet_address TEXT,
    mentor_id INTEGER, -- Ссылка на ID из таблицы mentors (будет создана ниже)
    referrer_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    referral_earnings DECIMAL(12,2) DEFAULT 0,
    last_activity TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Сервисы
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    icon TEXT DEFAULT '🔹',
    description TEXT,
    manual_link TEXT,
    bot_link TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Ресурсы
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content_link TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('community', 'resource')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Наставники (Зависит от users)
CREATE TABLE mentors (
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

-- 5. Профиты (Зависит от users)
CREATE TABLE profits (
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

-- 6. Реферальные начисления (Зависит от users и profits)
CREATE TABLE referral_profits (
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

-- 7. Начисления наставникам (Зависит от mentors, users, profits)
CREATE TABLE mentor_profits (
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

-- 8. Логи админов
CREATE TABLE admin_logs (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    admin_username TEXT,
    action_type TEXT NOT NULL,
    action_details TEXT,
    target_user_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. История рангов
CREATE TABLE rank_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_rank TEXT NOT NULL,
    new_rank TEXT NOT NULL,
    old_level INTEGER NOT NULL,
    new_level INTEGER NOT NULL,
    total_profit DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Уведомления
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Настройки бота
CREATE TABLE bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

-- 12. Настройки платежей
CREATE TABLE direct_payment_settings (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    requisites TEXT NOT NULL,
    additional_info TEXT,
    support_username TEXT NOT NULL
);

-- ====================================================================================
-- ЧАСТЬ 3: ИНДЕКСЫ
-- ====================================================================================

CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_profits_worker ON profits(worker_id);
CREATE INDEX idx_profits_status ON profits(status);
CREATE INDEX idx_profits_created ON profits(created_at DESC);
CREATE INDEX idx_mentors_active ON mentors(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_referral_profits_referrer ON referral_profits(referrer_id);
CREATE INDEX idx_referral_profits_status ON referral_profits(status);
CREATE INDEX idx_mentor_profits_mentor ON mentor_profits(mentor_user_id);
CREATE INDEX idx_mentor_profits_status ON mentor_profits(status);

-- ====================================================================================
-- ЧАСТЬ 4: VIEWS (ПРЕДСТАВЛЕНИЯ)
-- ====================================================================================

CREATE OR REPLACE VIEW mentor_details AS
SELECT 
    m.id,
    m.user_id,
    u.username,
    u.full_name,
    m.service_name,
    m.percent,
    m.rating,
    m.students_count,
    m.total_earned,
    m.is_active,
    m.created_at
FROM mentors m
JOIN users u ON m.user_id = u.id
WHERE m.is_active = TRUE;

-- ====================================================================================
-- ЧАСТЬ 5: ФУНКЦИИ (LOGIC)
-- ====================================================================================

-- 1. Статистика пользователя
CREATE OR REPLACE FUNCTION get_user_stats(p_user_id BIGINT)
RETURNS TABLE (
    total_count BIGINT,
    total_profit DECIMAL,
    avg_profit DECIMAL,
    max_profit DECIMAL,
    month_profit DECIMAL,
    week_profit DECIMAL,
    day_profit DECIMAL
) AS $$
SELECT 
    COUNT(*)::BIGINT,
    COALESCE(SUM(net_profit), 0)::DECIMAL,
    COALESCE(AVG(net_profit), 0)::DECIMAL,
    COALESCE(MAX(net_profit), 0)::DECIMAL,
    COALESCE(SUM(net_profit) FILTER (WHERE created_at >= DATE_TRUNC('month', NOW())), 0)::DECIMAL,
    COALESCE(SUM(net_profit) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days'), 0)::DECIMAL,
    COALESCE(SUM(net_profit) FILTER (WHERE DATE(created_at) = CURRENT_DATE), 0)::DECIMAL
FROM profits
WHERE worker_id = p_user_id;
$$ LANGUAGE sql STABLE;

-- 2. Топ воркеров
CREATE OR REPLACE FUNCTION get_top_workers(
    p_period TEXT DEFAULT 'all',
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    user_id BIGINT,
    full_name TEXT,
    username TEXT,
    total_profit DECIMAL,
    profit_count BIGINT
) AS $$
SELECT 
    u.id,
    u.full_name,
    u.username,
    COALESCE(SUM(p.net_profit), 0)::DECIMAL,
    COUNT(p.id)::BIGINT
FROM users u
LEFT JOIN profits p ON u.id = p.worker_id
    AND CASE p_period
        WHEN 'day' THEN DATE(p.created_at) = CURRENT_DATE
        WHEN 'week' THEN p.created_at >= NOW() - INTERVAL '7 days'
        WHEN 'month' THEN p.created_at >= DATE_TRUNC('month', NOW())
        ELSE TRUE
    END
WHERE u.status = 'active'
GROUP BY u.id, u.full_name, u.username
HAVING COALESCE(SUM(p.net_profit), 0) > 0
ORDER BY COALESCE(SUM(p.net_profit), 0) DESC
LIMIT p_limit;
$$ LANGUAGE sql STABLE;

-- 3. Позиция в рейтинге (Сложная логика с рангами)
CREATE OR REPLACE FUNCTION get_user_position(p_user_id BIGINT)
RETURNS TABLE (
    overall_rank BIGINT,
    overall_profit DECIMAL,
    monthly_rank BIGINT,
    monthly_profit DECIMAL,
    total_users BIGINT,
    user_avg_profit DECIMAL,
    team_avg_profit DECIMAL
) AS $$
DECLARE
    v_overall_rank BIGINT;
    v_overall_profit DECIMAL;
    v_monthly_rank BIGINT;
    v_monthly_profit DECIMAL;
    v_total_users BIGINT;
    v_user_avg DECIMAL;
    v_team_avg DECIMAL;
BEGIN
    -- Общий ранг
    SELECT r.rank, r.profit INTO v_overall_rank, v_overall_profit
    FROM (
        SELECT 
            u.id,
            COALESCE(SUM(p.net_profit), 0) as profit,
            ROW_NUMBER() OVER (ORDER BY COALESCE(SUM(p.net_profit), 0) DESC) as rank
        FROM users u
        LEFT JOIN profits p ON u.id = p.worker_id
        WHERE u.status = 'active'
        GROUP BY u.id
    ) r WHERE r.id = p_user_id;

    -- Месячный ранг
    SELECT r.rank, r.profit INTO v_monthly_rank, v_monthly_profit
    FROM (
        SELECT 
            u.id,
            COALESCE(SUM(p.net_profit), 0) as profit,
            ROW_NUMBER() OVER (ORDER BY COALESCE(SUM(p.net_profit), 0) DESC) as rank
        FROM users u
        LEFT JOIN profits p ON u.id = p.worker_id 
            AND p.created_at >= DATE_TRUNC('month', NOW())
        WHERE u.status = 'active'
        GROUP BY u.id
    ) r WHERE r.id = p_user_id;

    -- Общая статистика
    SELECT COUNT(*) INTO v_total_users FROM users WHERE status = 'active';
    SELECT COALESCE(AVG(net_profit), 0) INTO v_user_avg FROM profits WHERE worker_id = p_user_id;
    SELECT COALESCE(AVG(avg_p), 0) INTO v_team_avg FROM (SELECT AVG(net_profit) as avg_p FROM profits GROUP BY worker_id) s;

    RETURN QUERY SELECT 
        COALESCE(v_overall_rank, 0)::BIGINT,
        COALESCE(v_overall_profit, 0)::DECIMAL,
        COALESCE(v_monthly_rank, 0)::BIGINT,
        COALESCE(v_monthly_profit, 0)::DECIMAL,
        COALESCE(v_total_users, 0)::BIGINT,
        COALESCE(v_user_avg, 0)::DECIMAL,
        COALESCE(v_team_avg, 0)::DECIMAL;
END;
$$ LANGUAGE plpgsql STABLE;

-- 4. Статистика команды
CREATE OR REPLACE FUNCTION get_team_stats()
RETURNS TABLE (
    month_profit DECIMAL,
    day_profit DECIMAL,
    total_workers BIGINT,
    active_today BIGINT
) AS $$
SELECT 
    COALESCE(SUM(net_profit) FILTER (WHERE created_at >= DATE_TRUNC('month', NOW())), 0)::DECIMAL,
    COALESCE(SUM(net_profit) FILTER (WHERE DATE(created_at) = CURRENT_DATE), 0)::DECIMAL,
    (SELECT COUNT(*) FROM users WHERE status = 'active')::BIGINT,
    (SELECT COUNT(*) FROM users WHERE status = 'active' AND DATE(last_activity) = CURRENT_DATE)::BIGINT
FROM profits;
$$ LANGUAGE sql STABLE;

-- 5. Невыплаченные профиты воркеров (Для админки)
CREATE OR REPLACE FUNCTION get_unpaid_profits_summary()
RETURNS TABLE (
    user_id BIGINT,
    username TEXT,
    full_name TEXT,
    count BIGINT,
    total_unpaid DECIMAL
) AS $$
SELECT 
    u.id,
    u.username,
    u.full_name,
    COUNT(p.id)::BIGINT,
    SUM(p.net_profit)::DECIMAL
FROM users u
INNER JOIN profits p ON u.id = p.worker_id
WHERE p.status = 'hold'
GROUP BY u.id, u.username, u.full_name
ORDER BY SUM(p.net_profit) DESC;
$$ LANGUAGE sql STABLE;

-- 6. Невыплаченные реферальные (Для админки)
CREATE OR REPLACE FUNCTION get_unpaid_referral_summary()
RETURNS TABLE (
    user_id BIGINT,
    username TEXT,
    full_name TEXT,
    count BIGINT,
    total_unpaid DECIMAL
) AS $$
SELECT 
    u.id,
    u.username,
    u.full_name,
    COUNT(rp.id)::BIGINT,
    SUM(rp.amount)::DECIMAL
FROM users u
INNER JOIN referral_profits rp ON u.id = rp.referrer_id
WHERE rp.status = 'hold'
GROUP BY u.id, u.username, u.full_name
ORDER BY SUM(rp.amount) DESC;
$$ LANGUAGE sql STABLE;

-- 7. Невыплаченные менторские (Для админки)
CREATE OR REPLACE FUNCTION get_unpaid_mentor_summary()
RETURNS TABLE (
    user_id BIGINT,
    username TEXT,
    full_name TEXT,
    count BIGINT,
    total_unpaid DECIMAL
) AS $$
SELECT 
    u.id,
    u.username,
    u.full_name,
    COUNT(mp.id)::BIGINT,
    SUM(mp.amount)::DECIMAL
FROM users u
INNER JOIN mentor_profits mp ON u.id = mp.mentor_user_id
WHERE mp.status = 'hold'
GROUP BY u.id, u.username, u.full_name
ORDER BY SUM(mp.amount) DESC;
$$ LANGUAGE sql STABLE;

-- ====================================================================================
-- ЧАСТЬ 6: НАЧАЛЬНЫЕ ДАННЫЕ (SEED)
-- ====================================================================================

INSERT INTO bot_settings (key, value, description) VALUES
    ('maintenance_mode', 'false', 'Режим обслуживания'),
    ('welcome_message', 'Добро пожаловать!', 'Приветствие'),
    ('min_payout', '50', 'Мин. выплата USD')
ON CONFLICT (key) DO NOTHING;

INSERT INTO direct_payment_settings (id, requisites, additional_info, support_username) VALUES
    (1, 'Не настроено', 'Обратитесь к админу', 'support')
ON CONFLICT (id) DO NOTHING;

-- ====================================================================================
-- ГОТОВО! 
-- ====================================================================================
-- База данных полностью настроена и готова к использованию
-- Все таблицы, индексы, функции и начальные данные созданы
-- ====================================================================================