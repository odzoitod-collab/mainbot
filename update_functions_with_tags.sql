-- Обновление функций для работы с тегами
-- Выполнить в Supabase SQL Editor после add_tag_system.sql

-- ВАЖНО: Сначала удаляем существующие функции
DROP FUNCTION IF EXISTS get_top_workers(TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_user_position(BIGINT);
DROP FUNCTION IF EXISTS get_unpaid_profits_summary();
DROP FUNCTION IF EXISTS get_unpaid_referral_summary();
DROP FUNCTION IF EXISTS get_unpaid_mentor_summary();

-- Удаляем существующие views если есть
DROP VIEW IF EXISTS profits_with_tags;
DROP VIEW IF EXISTS mentor_details;

-- 1. Создаем функцию get_top_workers с поддержкой тегов
CREATE OR REPLACE FUNCTION get_top_workers(
    p_period TEXT DEFAULT 'all',
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    user_id BIGINT,
    full_name TEXT,
    username TEXT,
    user_tag TEXT,
    total_profit DECIMAL,
    profit_count BIGINT
) AS $$
SELECT 
    u.id,
    u.full_name,
    u.username,
    u.user_tag,
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
GROUP BY u.id, u.full_name, u.username, u.user_tag
HAVING COALESCE(SUM(p.net_profit), 0) > 0
ORDER BY COALESCE(SUM(p.net_profit), 0) DESC
LIMIT p_limit;
$$ LANGUAGE sql STABLE;

-- 2. Создаем функцию get_user_position с поддержкой тегов
CREATE OR REPLACE FUNCTION get_user_position(p_user_id BIGINT)
RETURNS TABLE (
    overall_rank BIGINT,
    overall_profit DECIMAL,
    monthly_rank BIGINT,
    monthly_profit DECIMAL,
    total_users BIGINT,
    user_avg_profit DECIMAL,
    team_avg_profit DECIMAL,
    user_tag TEXT
) AS $$
WITH overall_stats AS (
    SELECT 
        u.id,
        u.user_tag,
        COALESCE(SUM(p.net_profit), 0) as total_profit,
        ROW_NUMBER() OVER (ORDER BY COALESCE(SUM(p.net_profit), 0) DESC) as rank
    FROM users u
    LEFT JOIN profits p ON u.id = p.worker_id
    WHERE u.status = 'active'
    GROUP BY u.id, u.user_tag
),
monthly_stats AS (
    SELECT 
        u.id,
        COALESCE(SUM(p.net_profit), 0) as month_profit,
        ROW_NUMBER() OVER (ORDER BY COALESCE(SUM(p.net_profit), 0) DESC) as rank
    FROM users u
    LEFT JOIN profits p ON u.id = p.worker_id 
        AND p.created_at >= DATE_TRUNC('month', NOW())
    WHERE u.status = 'active'
    GROUP BY u.id
),
team_avg AS (
    SELECT AVG(total_profit) as avg_profit
    FROM (
        SELECT COALESCE(SUM(p.net_profit), 0) as total_profit
        FROM users u
        LEFT JOIN profits p ON u.id = p.worker_id
        WHERE u.status = 'active'
        GROUP BY u.id
    ) t
)
SELECT 
    o.rank::BIGINT,
    o.total_profit::DECIMAL,
    m.rank::BIGINT,
    m.month_profit::DECIMAL,
    (SELECT COUNT(*) FROM users WHERE status = 'active')::BIGINT,
    o.total_profit::DECIMAL as user_avg,
    (SELECT avg_profit FROM team_avg)::DECIMAL,
    o.user_tag
FROM overall_stats o
JOIN monthly_stats m ON o.id = m.id
WHERE o.id = p_user_id;
$$ LANGUAGE sql STABLE;

-- 3. Создаем view для отображения профитов с тегами
CREATE OR REPLACE VIEW profits_with_tags AS
SELECT 
    p.id,
    p.worker_id,
    u.user_tag,
    u.full_name,
    u.username,
    p.amount,
    p.net_profit,
    p.service_name,
    p.status,
    p.created_at,
    p.paid_at
FROM profits p
JOIN users u ON p.worker_id = u.id;

-- 4. Функция для получения непроплаченных профитов с тегами
CREATE OR REPLACE FUNCTION get_unpaid_profits_summary()
RETURNS TABLE (
    worker_id BIGINT,
    user_tag TEXT,
    full_name TEXT,
    username TEXT,
    total_unpaid DECIMAL,
    profit_count BIGINT
) AS $$
SELECT 
    u.id,
    u.user_tag,
    u.full_name,
    u.username,
    COALESCE(SUM(p.net_profit), 0)::DECIMAL,
    COUNT(p.id)::BIGINT
FROM users u
JOIN profits p ON u.id = p.worker_id
WHERE p.status = 'hold'
GROUP BY u.id, u.user_tag, u.full_name, u.username
HAVING COUNT(p.id) > 0
ORDER BY COALESCE(SUM(p.net_profit), 0) DESC;
$$ LANGUAGE sql STABLE;

-- 5. Создаем view для наставников с тегами
CREATE OR REPLACE VIEW mentor_details AS
SELECT 
    m.id,
    m.user_id,
    u.user_tag,
    u.full_name,
    u.username,
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

-- 6. Функция для получения непроплаченных рефералов с тегами
CREATE OR REPLACE FUNCTION get_unpaid_referral_summary()
RETURNS TABLE (
    referrer_id BIGINT,
    referrer_tag TEXT,
    referrer_name TEXT,
    referrer_username TEXT,
    total_unpaid DECIMAL,
    profit_count BIGINT
) AS $$
SELECT 
    u.id,
    u.user_tag,
    u.full_name,
    u.username,
    COALESCE(SUM(rp.amount), 0)::DECIMAL,
    COUNT(rp.id)::BIGINT
FROM users u
JOIN referral_profits rp ON u.id = rp.referrer_id
WHERE rp.status = 'hold'
GROUP BY u.id, u.user_tag, u.full_name, u.username
HAVING COUNT(rp.id) > 0
ORDER BY COALESCE(SUM(rp.amount), 0) DESC;
$$ LANGUAGE sql STABLE;

-- 7. Функция для получения непроплаченных профитов наставников с тегами
CREATE OR REPLACE FUNCTION get_unpaid_mentor_summary()
RETURNS TABLE (
    mentor_user_id BIGINT,
    mentor_tag TEXT,
    mentor_name TEXT,
    mentor_username TEXT,
    total_unpaid DECIMAL,
    profit_count BIGINT
) AS $$
SELECT 
    u.id,
    u.user_tag,
    u.full_name,
    u.username,
    COALESCE(SUM(mp.amount), 0)::DECIMAL,
    COUNT(mp.id)::BIGINT
FROM users u
JOIN mentor_profits mp ON u.id = mp.mentor_user_id
WHERE mp.status = 'hold'
GROUP BY u.id, u.user_tag, u.full_name, u.username
HAVING COUNT(mp.id) > 0
ORDER BY COALESCE(SUM(mp.amount), 0) DESC;
$$ LANGUAGE sql STABLE;