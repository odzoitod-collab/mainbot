-- ============================================
-- ОЧИСТКА - выполнить ПЕРВЫМ
-- ============================================

-- Удаляем функции
DROP FUNCTION IF EXISTS get_user_stats(BIGINT);
DROP FUNCTION IF EXISTS get_top_workers(TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_user_position(BIGINT);
DROP FUNCTION IF EXISTS get_team_stats();
DROP FUNCTION IF EXISTS get_unpaid_profits_summary();

-- Удаляем views
DROP VIEW IF EXISTS mentor_details;
DROP VIEW IF EXISTS worker_stats;
DROP VIEW IF EXISTS active_workers_stats;
DROP VIEW IF EXISTS service_stats;

-- Удаляем таблицы (в правильном порядке из-за FK)
DROP TABLE IF EXISTS answers CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS user_action_logs CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS rank_history CASCADE;
DROP TABLE IF EXISTS admin_logs CASCADE;
DROP TABLE IF EXISTS profits CASCADE;
DROP TABLE IF EXISTS mentors CASCADE;
DROP TABLE IF EXISTS resources CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS direct_payment_settings CASCADE;
DROP TABLE IF EXISTS bot_settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Удаляем типы если есть
DROP TYPE IF EXISTS user_status CASCADE;
DROP TYPE IF EXISTS profit_status CASCADE;
DROP TYPE IF EXISTS resource_type CASCADE;
DROP TYPE IF EXISTS admin_action_type CASCADE;
DROP TYPE IF EXISTS notification_type CASCADE;
DROP TYPE IF EXISTS user_action_type CASCADE;
