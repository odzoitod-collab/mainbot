-- Скрипт для очистки функций перед обновлением
-- Выполнить ПЕРЕД update_functions_with_tags.sql если возникают ошибки

-- Удаляем все функции связанные с тегами
DROP FUNCTION IF EXISTS get_top_workers(TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_user_position(BIGINT);
DROP FUNCTION IF EXISTS get_unpaid_profits_summary();
DROP FUNCTION IF EXISTS get_unpaid_referral_summary();
DROP FUNCTION IF EXISTS get_unpaid_mentor_summary();

-- Удаляем views
DROP VIEW IF EXISTS profits_with_tags;
DROP VIEW IF EXISTS mentor_details;

-- Если нужно полностью откатить систему тегов:
-- ALTER TABLE users DROP COLUMN IF EXISTS user_tag;
-- DROP FUNCTION IF EXISTS generate_next_tag();
-- DROP FUNCTION IF EXISTS assign_user_tag();
-- DROP TRIGGER IF EXISTS trigger_assign_user_tag ON users;