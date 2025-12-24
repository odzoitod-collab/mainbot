# Telegram Bot - Worker Team Management

Бот для управления командой с Supabase.

## Быстрый старт

### 1. Supabase

1. Создай проект на [supabase.com](https://supabase.com)
2. SQL Editor → выполни `supabase_schema.sql`
3. Settings → API → скопируй URL и ключи

### 2. Настройка

```bash
# .env
BOT_TOKEN=your_bot_token
ADMIN_IDS=123456789,987654321
LOG_CHANNEL_ID=-100...
APPLICATION_CHANNEL_ID=-100...
CHAT_GROUP_ID=-100...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
```

### 3. Запуск

```bash
pip install -r requirements.txt
python main.py
```

### Docker

```bash
docker-compose up -d
```

## Структура

```
├── main.py              # Entry point
├── config.py            # Configuration
├── database/
│   └── db.py            # All Supabase operations
├── handlers/            # Bot handlers
├── keyboards/           # Inline keyboards
├── middlewares/         # Middleware
├── states/              # FSM states
├── utils/               # Helpers
└── images/              # Brand images
```

## Функции

- ✅ Регистрация с анкетой
- ✅ Система менторства
- ✅ Профиты и выплаты
- ✅ Ранги с бонусами
- ✅ Админ панель
- ✅ Рассылки
- ✅ Статистика и рейтинги
