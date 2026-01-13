-- ============================================
-- MENTOR PANEL SYSTEM - DATABASE SCHEMA
-- ============================================

-- Добавляем поле для ТГК наставника в таблицу mentors
ALTER TABLE mentors 
ADD COLUMN IF NOT EXISTS telegram_channel TEXT,
ADD COLUMN IF NOT EXISTS channel_description TEXT,
ADD COLUMN IF NOT EXISTS channel_invite_link TEXT;

-- Таблица для рассылок наставников
CREATE TABLE IF NOT EXISTS mentor_broadcasts (
    id SERIAL PRIMARY KEY,
    mentor_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    message_type TEXT NOT NULL DEFAULT 'text' CHECK (message_type IN ('text', 'photo', 'video')),
    media_file_id TEXT,
    sent_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sending', 'completed', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Таблица для отслеживания получателей рассылки
CREATE TABLE IF NOT EXISTS mentor_broadcast_recipients (
    id SERIAL PRIMARY KEY,
    broadcast_id INTEGER NOT NULL REFERENCES mentor_broadcasts(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    UNIQUE(broadcast_id, student_id)
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_mentor_broadcasts_mentor ON mentor_broadcasts(mentor_user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_broadcasts_status ON mentor_broadcasts(status);
CREATE INDEX IF NOT EXISTS idx_mentor_broadcast_recipients_broadcast ON mentor_broadcast_recipients(broadcast_id);
CREATE INDEX IF NOT EXISTS idx_mentor_broadcast_recipients_status ON mentor_broadcast_recipients(status);

-- Функция для получения студентов наставника
CREATE OR REPLACE FUNCTION get_mentor_students(mentor_user_id_param BIGINT)
RETURNS TABLE (
    student_id BIGINT,
    student_tag TEXT,
    username TEXT,
    full_name TEXT,
    total_profit DECIMAL(12,2),
    last_activity TIMESTAMPTZ,
    mentor_earnings DECIMAL(12,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as student_id,
        u.user_tag as student_tag,
        u.username,
        u.full_name,
        COALESCE(stats.total_profit, 0) as total_profit,
        u.last_activity,
        COALESCE(mentor_earnings.total_earned, 0) as mentor_earnings
    FROM users u
    INNER JOIN mentors m ON u.mentor_id = m.id
    LEFT JOIN (
        SELECT 
            worker_id,
            SUM(net_profit) as total_profit
        FROM profits 
        GROUP BY worker_id
    ) stats ON u.id = stats.worker_id
    LEFT JOIN (
        SELECT 
            student_id,
            SUM(amount) as total_earned
        FROM mentor_profits mp
        WHERE mp.mentor_user_id = mentor_user_id_param
        GROUP BY student_id
    ) mentor_earnings ON u.id = mentor_earnings.student_id
    WHERE m.user_id = mentor_user_id_param
    ORDER BY stats.total_profit DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения статистики наставника
CREATE OR REPLACE FUNCTION get_mentor_stats(mentor_user_id_param BIGINT)
RETURNS TABLE (
    total_students INTEGER,
    active_students INTEGER,
    total_earned DECIMAL(12,2),
    this_month_earned DECIMAL(12,2),
    avg_student_profit DECIMAL(12,2),
    top_student_profit DECIMAL(12,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT u.id)::INTEGER as total_students,
        COUNT(DISTINCT CASE WHEN u.last_activity > NOW() - INTERVAL '7 days' THEN u.id END)::INTEGER as active_students,
        COALESCE(SUM(mp.amount), 0) as total_earned,
        COALESCE(SUM(CASE WHEN mp.created_at > DATE_TRUNC('month', NOW()) THEN mp.amount ELSE 0 END), 0) as this_month_earned,
        COALESCE(AVG(student_profits.total_profit), 0) as avg_student_profit,
        COALESCE(MAX(student_profits.total_profit), 0) as top_student_profit
    FROM mentors m
    LEFT JOIN users u ON u.mentor_id = m.id
    LEFT JOIN mentor_profits mp ON mp.mentor_user_id = mentor_user_id_param AND mp.student_id = u.id
    LEFT JOIN (
        SELECT 
            worker_id,
            SUM(net_profit) as total_profit
        FROM profits 
        GROUP BY worker_id
    ) student_profits ON u.id = student_profits.worker_id
    WHERE m.user_id = mentor_user_id_param;
END;
$$ LANGUAGE plpgsql;

-- Функция для проверки является ли пользователь наставником
CREATE OR REPLACE FUNCTION is_user_mentor(user_id_param BIGINT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM mentors 
        WHERE user_id = user_id_param AND is_active = TRUE
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE mentor_broadcasts IS 'Рассылки наставников своим студентам';
COMMENT ON TABLE mentor_broadcast_recipients IS 'Получатели рассылок наставников';
COMMENT ON FUNCTION get_mentor_students IS 'Получить список студентов наставника с статистикой';
COMMENT ON FUNCTION get_mentor_stats IS 'Получить общую статистику наставника';
COMMENT ON FUNCTION is_user_mentor IS 'Проверить является ли пользователь активным наставником';