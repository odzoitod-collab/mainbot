-- ============================================
-- FIX: get_mentor_students function
-- Исправление конфликта имен student_id
-- ============================================

-- Удаляем старую функцию
DROP FUNCTION IF EXISTS get_mentor_students(BIGINT);

-- Создаем исправленную функцию
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
        u.id,
        u.user_tag,
        u.username,
        u.full_name,
        COALESCE(stats.total_profit, 0),
        u.last_activity,
        COALESCE(mentor_earnings_data.total_earned, 0)
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
            mp.student_id as stud_id,
            SUM(mp.amount) as total_earned
        FROM mentor_profits mp
        WHERE mp.mentor_user_id = mentor_user_id_param
        GROUP BY mp.student_id
    ) mentor_earnings_data ON u.id = mentor_earnings_data.stud_id
    WHERE m.user_id = mentor_user_id_param
    ORDER BY stats.total_profit DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- Проверка
SELECT 'Function get_mentor_students fixed successfully!' as status;