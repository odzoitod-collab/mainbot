-- ============================================
-- TELEGRAM BOT - FUNCTIONS & VIEWS
-- ============================================
-- Один файл - всё работает сразу
-- ============================================

-- ============================================
-- ТАБЛИЦЫ (если нет)
-- ============================================

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

CREATE INDEX IF NOT EXISTS idx_referral_profits_referrer ON referral_profits(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_profits_status ON referral_profits(status);
CREATE INDEX IF NOT EXISTS idx_mentor_profits_mentor ON mentor_profits(mentor_user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_profits_status ON mentor_profits(status);

-- ============================================
-- VIEWS
-- ============================================

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

-- ============================================
-- ФУНКЦИИ
-- ============================================

-- Статистика пользователя
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

-- Топ воркеров
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

-- Позиция в рейтинге
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

    SELECT COUNT(*) INTO v_total_users FROM users WHERE status = 'active';
    SELECT COALESCE(AVG(net_profit), 0) INTO v_user_avg FROM profits WHERE worker_id = p_user_id;
    SELECT COALESCE(AVG(avg_p), 0) INTO v_team_avg FROM (SELECT AVG(net_profit) as avg_p FROM profits GROUP BY worker_id) s;

    RETURN QUERY SELECT 
        COALESCE(v_overall_rank, v_total_users)::BIGINT,
        COALESCE(v_overall_profit, 0)::DECIMAL,
        COALESCE(v_monthly_rank, v_total_users)::BIGINT,
        COALESCE(v_monthly_profit, 0)::DECIMAL,
        COALESCE(v_total_users, 0)::BIGINT,
        COALESCE(v_user_avg, 0)::DECIMAL,
        COALESCE(v_team_avg, 0)::DECIMAL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Статистика команды
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

-- Невыплаченные профиты воркеров
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

-- Невыплаченные реферальные профиты
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

-- Невыплаченные профиты наставников
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

-- ============================================
-- ГОТОВО!
-- ============================================
