-- Добавление системы тегов
-- Выполнить эти команды в Supabase SQL Editor

-- 1. Добавляем поле для тега в таблицу users
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_tag TEXT UNIQUE;

-- 2. Создаем индекс для быстрого поиска по тегу
CREATE INDEX IF NOT EXISTS idx_users_tag ON users(user_tag);

-- 3. Создаем функцию для генерации следующего тега
CREATE OR REPLACE FUNCTION generate_next_tag()
RETURNS TEXT AS $$
DECLARE
    next_number INTEGER;
    new_tag TEXT;
BEGIN
    -- Находим максимальный номер тега
    SELECT COALESCE(MAX(CAST(SUBSTRING(user_tag FROM '#irl_(\d+)') AS INTEGER)), 0) + 1
    INTO next_number
    FROM users
    WHERE user_tag ~ '^#irl_\d+$';
    
    -- Генерируем новый тег
    new_tag := '#irl_' || next_number;
    
    RETURN new_tag;
END;
$$ LANGUAGE plpgsql;

-- 4. Создаем функцию для автоматического назначения тега при регистрации
CREATE OR REPLACE FUNCTION assign_user_tag()
RETURNS TRIGGER AS $$
BEGIN
    -- Если тег не задан, генерируем новый
    IF NEW.user_tag IS NULL THEN
        NEW.user_tag := generate_next_tag();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. Создаем триггер для автоматического назначения тега
DROP TRIGGER IF EXISTS trigger_assign_user_tag ON users;
CREATE TRIGGER trigger_assign_user_tag
    BEFORE INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION assign_user_tag();

-- 6. Назначаем теги существующим пользователям (если есть)
DO $$
DECLARE
    user_record RECORD;
    tag_counter INTEGER := 1;
BEGIN
    FOR user_record IN 
        SELECT id FROM users WHERE user_tag IS NULL ORDER BY created_at
    LOOP
        UPDATE users 
        SET user_tag = '#irl_' || tag_counter 
        WHERE id = user_record.id;
        
        tag_counter := tag_counter + 1;
    END LOOP;
END $$;