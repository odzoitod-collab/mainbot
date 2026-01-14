# ИСПРАВЛЕНИЕ КНОПКИ "МОИ СТУДЕНТЫ"

## ✅ Что исправлено

### 🐛 Проблема
Кнопка "👥 Мои студенты" в панели наставников не работала из-за ошибки в SQL функции:
```
column reference "student_id" is ambiguous
It could refer to either a PL/pgSQL variable or a table column.
```

### 🔧 Причина
В SQL функции `get_mentor_students` был конфликт имен:
- Выходной параметр функции: `student_id`
- Колонка в подзапросе: `student_id`

PostgreSQL не мог определить к какому `student_id` обращаться.

### ✅ Решение

#### 1. Исправлена SQL функция
**Было (неправильно):**
```sql
LEFT JOIN (
    SELECT 
        student_id,  -- ❌ Конфликт с выходным параметром
        SUM(amount) as total_earned
    FROM mentor_profits mp
    WHERE mp.mentor_user_id = mentor_user_id_param
    GROUP BY student_id
) mentor_earnings ON u.id = mentor_earnings.student_id
```

**Стало (правильно):**
```sql
LEFT JOIN (
    SELECT 
        mp.student_id as stud_id,  -- ✅ Уникальное имя
        SUM(mp.amount) as total_earned
    FROM mentor_profits mp
    WHERE mp.mentor_user_id = mentor_user_id_param
    GROUP BY mp.student_id
) mentor_earnings_data ON u.id = mentor_earnings_data.stud_id
```

#### 2. Убраны алиасы в SELECT
**Было:**
```sql
SELECT 
    u.id as student_id,
    u.user_tag as student_tag,
    ...
```

**Стало:**
```sql
SELECT 
    u.id,
    u.user_tag,
    ...
```

Имена колонок берутся из RETURNS TABLE автоматически.

#### 3. Добавлено логирование
В Python функции:
```python
logger.info(f"get_mentor_students for {mentor_user_id}: {len(result.data or [])} students")
```

В обработчике:
```python
logger.info(f"User {callback.from_user.id} viewing mentor students")
logger.info(f"Found {len(students)} students")
```

#### 4. Добавлена обработка ошибок
```python
try:
    students = await get_mentor_students(callback.from_user.id)
    # ...
except Exception as e:
    logger.error(f"Error showing mentor students: {e}")
    await callback.message.edit_text("❌ Ошибка загрузки...")
```

## 🔧 Как применить исправление

### Вариант 1: Быстрое исправление (рекомендуется)
Выполните SQL скрипт `fix_mentor_students_function.sql`:

```bash
# Через psql
psql -h your_host -U postgres -d postgres -f fix_mentor_students_function.sql

# Или через Supabase Dashboard:
# 1. Откройте SQL Editor
# 2. Скопируйте содержимое fix_mentor_students_function.sql
# 3. Выполните запрос
```

### Вариант 2: Полное обновление
Выполните обновленный `mentor_panel_system.sql`:

```bash
psql -h your_host -U postgres -d postgres -f mentor_panel_system.sql
```

### Вариант 3: Ручное исправление
Выполните в SQL Editor:

```sql
DROP FUNCTION IF EXISTS get_mentor_students(BIGINT);

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
```

## 🧪 Тестирование

### После применения исправления:

1. **Перезапустите бота:**
```bash
python main.py
```

2. **Проверьте в боте:**
   - Откройте "👨‍🏫 Панель наставника"
   - Нажмите "👥 Мои студенты"
   - Должен открыться список студентов

3. **Проверьте логи:**
```
INFO - User 123456 viewing mentor students
INFO - get_mentor_students for 123456: 0 students
INFO - Found 0 students for mentor 123456
```

### Если студентов нет:
Это нормально! Показывается сообщение:
```
👥 МОИ СТУДЕНТЫ

У вас пока нет студентов.
```

### Если есть студенты:
Показывается список:
```
👥 МОИ СТУДЕНТЫ

Стр. 1/1 • Всего: 3

1. #irl_worker1
   💰 Профит: 1500.00 RUB
   💵 Ваш доход: 150.00 RUB
   📊 🟢 Активен

2. #irl_worker2
   💰 Профит: 800.00 RUB
   💵 Ваш доход: 80.00 RUB
   📊 🔴 Неактивен
```

## 📊 Что показывается

### Для каждого студента:
- **Тег** - уникальный тег студента (#irl_xxx)
- **Профит** - общий профит студента
- **Ваш доход** - сколько вы заработали с этого студента
- **Статус** - активен (🟢) или неактивен (🔴)

### Критерии активности:
- 🟢 **Активен** - был активен в последние 7 дней
- 🔴 **Неактивен** - не был активен более 7 дней

### Пагинация:
- По 5 студентов на страницу
- Кнопки "⬅️ Назад" и "Вперед ➡️"
- Показывается текущая страница

## 🐛 Решение проблем

### Ошибка "column reference is ambiguous"
**Причина:** Старая версия функции

**Решение:** Выполните `fix_mentor_students_function.sql`

### Кнопка не реагирует
**Причина:** Роутер не зарегистрирован

**Решение:**
```python
# В main.py должно быть:
dp.include_router(mentor_panel_router)
```

### Показывает "Ошибка загрузки"
**Причина:** Проблема с базой данных

**Решение:**
1. Проверьте логи бота
2. Проверьте что функция создана: `SELECT * FROM pg_proc WHERE proname = 'get_mentor_students';`
3. Проверьте права доступа к таблицам

### Студенты не отображаются
**Причина:** Нет студентов или они не выбрали наставника

**Решение:**
1. Проверьте что у пользователей установлен `mentor_id`
2. Проверьте что `mentor_id` соответствует ID наставника в таблице `mentors`
3. Выполните запрос:
```sql
SELECT u.id, u.full_name, u.mentor_id, m.user_id as mentor_user_id
FROM users u
LEFT JOIN mentors m ON u.mentor_id = m.id
WHERE m.user_id = YOUR_USER_ID;
```

## 📋 Структура данных

### Возвращаемые поля:
```python
{
    'student_id': 123456,
    'student_tag': '#irl_worker1',
    'username': 'username',
    'full_name': 'Имя студента',
    'total_profit': 1500.00,
    'last_activity': '2024-01-14T10:30:00Z',
    'mentor_earnings': 150.00
}
```

### Расчет доходов:
- `total_profit` - сумма всех профитов студента
- `mentor_earnings` - сумма начислений наставнику от этого студента
- Берется из таблицы `mentor_profits`

## ✅ Итог

Кнопка "👥 Мои студенты" теперь работает:
1. ✅ Исправлен конфликт имен в SQL функции
2. ✅ Добавлено логирование для отладки
3. ✅ Добавлена обработка ошибок
4. ✅ Показывается список студентов с статистикой
5. ✅ Работает пагинация
6. ✅ Показывается статус активности

После выполнения SQL скрипта кнопка будет работать корректно!