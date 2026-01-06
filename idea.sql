-- Обновленная схема для идей с категориями и улучшенным функционалом

-- 1. Обновляем таблицу идей (добавляем категорию)
ALTER TABLE ideas ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'Идея';

-- 2. Создаем индексы для лучшей производительности
CREATE INDEX IF NOT EXISTS idx_ideas_votes ON ideas(votes_count DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_created ON ideas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_category ON ideas(category);
CREATE INDEX IF NOT EXISTS idx_ideas_user ON ideas(user_id);

-- 3. Обновляем функцию голосования с улучшенной логикой
DROP FUNCTION IF EXISTS toggle_vote(bigint, text);
CREATE OR REPLACE FUNCTION toggle_vote(row_id bigint, user_tg_id text)
RETURNS TABLE(new_votes_count int, user_liked boolean) AS $$
DECLARE
  is_liked boolean;
  new_count int;
BEGIN
  -- Проверяем, есть ли юзер в массиве liked_by
  SELECT user_tg_id = ANY(liked_by) INTO is_liked FROM ideas WHERE id = row_id;

  IF is_liked THEN
    -- Убираем лайк
    UPDATE ideas 
    SET votes_count = votes_count - 1,
        liked_by = array_remove(liked_by, user_tg_id)
    WHERE id = row_id
    RETURNING votes_count INTO new_count;
    
    RETURN QUERY SELECT new_count, false;
  ELSE
    -- Ставим лайк
    UPDATE ideas 
    SET votes_count = votes_count + 1,
        liked_by = array_append(liked_by, user_tg_id)
    WHERE id = row_id
    RETURNING votes_count INTO new_count;
    
    RETURN QUERY SELECT new_count, true;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- 4. Функция для получения статистики идей
CREATE OR REPLACE FUNCTION get_ideas_stats()
RETURNS TABLE(
  total_ideas bigint,
  total_votes bigint,
  top_ideas bigint,
  new_ideas bigint,
  categories_count bigint
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(*) as total_ideas,
    COALESCE(SUM(votes_count), 0) as total_votes,
    COUNT(*) FILTER (WHERE votes_count >= 5) as top_ideas,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as new_ideas,
    COUNT(DISTINCT category) as categories_count
  FROM ideas;
END;
$$ LANGUAGE plpgsql;

-- 5. Функция для получения топ идей по категориям
CREATE OR REPLACE FUNCTION get_top_ideas_by_category(category_name text DEFAULT NULL, limit_count int DEFAULT 10)
RETURNS TABLE(
  id bigint,
  user_id text,
  user_name text,
  content text,
  category text,
  votes_count int,
  liked_by text[],
  created_at timestamptz
) AS $$
BEGIN
  IF category_name IS NULL THEN
    RETURN QUERY
    SELECT i.id, i.user_id, i.user_name, i.content, i.category, i.votes_count, i.liked_by, i.created_at
    FROM ideas i
    ORDER BY i.votes_count DESC, i.created_at DESC
    LIMIT limit_count;
  ELSE
    RETURN QUERY
    SELECT i.id, i.user_id, i.user_name, i.content, i.category, i.votes_count, i.liked_by, i.created_at
    FROM ideas i
    WHERE i.category = category_name
    ORDER BY i.votes_count DESC, i.created_at DESC
    LIMIT limit_count;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- 6. Включаем Row Level Security (если еще не включено)
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;

-- 7. Обновляем политики безопасности
DROP POLICY IF EXISTS "Enable read access for all users" ON ideas;
DROP POLICY IF EXISTS "Enable insert for all users" ON ideas;
DROP POLICY IF EXISTS "Enable update for vote logic" ON ideas;

CREATE POLICY "Enable read access for all users" ON ideas FOR SELECT USING (true);
CREATE POLICY "Enable insert for all users" ON ideas FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for vote logic" ON ideas FOR UPDATE USING (true);

-- 8. Создаем view для удобного получения идей с дополнительной информацией
CREATE OR REPLACE VIEW ideas_with_stats AS
SELECT 
  i.*,
  CASE 
    WHEN i.created_at > NOW() - INTERVAL '24 hours' THEN true 
    ELSE false 
  END as is_new,
  CASE 
    WHEN i.votes_count >= 10 THEN 'hot'
    WHEN i.votes_count >= 5 THEN 'popular'
    WHEN i.created_at > NOW() - INTERVAL '24 hours' THEN 'new'
    ELSE 'normal'
  END as status,
  ROW_NUMBER() OVER (ORDER BY i.votes_count DESC, i.created_at DESC) as rank
FROM ideas i;

-- 9. Функция для уведомлений о новых идеях (для будущего использования)
CREATE OR REPLACE FUNCTION notify_new_idea()
RETURNS TRIGGER AS $$
BEGIN
  -- Отправляем уведомление через PostgreSQL NOTIFY
  PERFORM pg_notify('new_idea', json_build_object(
    'id', NEW.id,
    'user_name', NEW.user_name,
    'category', NEW.category,
    'content', LEFT(NEW.content, 100)
  )::text);
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 10. Создаем триггер для уведомлений
DROP TRIGGER IF EXISTS trigger_notify_new_idea ON ideas;
CREATE TRIGGER trigger_notify_new_idea
  AFTER INSERT ON ideas
  FOR EACH ROW
  EXECUTE FUNCTION notify_new_idea();

-- 11. Добавляем комментарии к таблице и колонкам
COMMENT ON TABLE ideas IS 'Таблица идей и предложений от пользователей';
COMMENT ON COLUMN ideas.id IS 'Уникальный идентификатор идеи';
COMMENT ON COLUMN ideas.user_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN ideas.user_name IS 'Имя пользователя (username или first_name)';
COMMENT ON COLUMN ideas.content IS 'Текст идеи или предложения';
COMMENT ON COLUMN ideas.category IS 'Категория идеи (Идея, Сервис, Баг, и т.д.)';
COMMENT ON COLUMN ideas.votes_count IS 'Количество лайков/голосов';
COMMENT ON COLUMN ideas.liked_by IS 'Массив ID пользователей, которые лайкнули';
COMMENT ON COLUMN ideas.created_at IS 'Дата и время создания идеи';