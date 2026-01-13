-- Скрипт для проверки работы системы тегов
-- Выполнить после установки для проверки

-- 1. Проверяем что поле user_tag добавлено
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'user_tag';

-- 2. Проверяем что функция генерации тегов работает
SELECT generate_next_tag();

-- 3. Проверяем что у пользователей есть теги
SELECT id, full_name, user_tag 
FROM users 
WHERE user_tag IS NOT NULL 
LIMIT 5;

-- 4. Проверяем функцию get_top_workers с тегами
SELECT * FROM get_top_workers('all', 5);

-- 5. Проверяем что триггер работает (создаем тестового пользователя)
-- ВНИМАНИЕ: Этот пользователь будет создан в базе!
-- INSERT INTO users (id, full_name, username, status) 
-- VALUES (999999999, 'Test User', 'testuser', 'active');

-- Проверяем что тег назначился автоматически
-- SELECT id, full_name, user_tag FROM users WHERE id = 999999999;

-- Удаляем тестового пользователя
-- DELETE FROM users WHERE id = 999999999;

-- 6. Проверяем уникальность тегов
SELECT user_tag, COUNT(*) as count
FROM users 
WHERE user_tag IS NOT NULL
GROUP BY user_tag
HAVING COUNT(*) > 1;