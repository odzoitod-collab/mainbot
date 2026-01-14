# Добавление фото ко всем командам в чате

## Изменения

Теперь все команды в чате автоматически отправляются с фото (по умолчанию `images/ирл.jpg`).

## Как это работает

Функция `reply_with_auto_delete()` была улучшена:

### Было:
```python
async def reply_with_auto_delete(
    message: Message,
    text: str,
    delay: int = 10,
    delete_original: bool = True,
    **kwargs
) -> Message:
    # Отправляла только текст
    sent_message = await message.reply(text, **kwargs)
    ...
```

### Стало:
```python
async def reply_with_auto_delete(
    message: Message,
    text: str,
    delay: int = 10,
    delete_original: bool = True,
    use_photo: bool = True,  # Новый параметр
    default_photo_path: str = "images/ирл.jpg",  # Путь к дефолтному фото
    **kwargs
) -> Message:
    # Сначала пытается отправить с фото
    if use_photo:
        try:
            from aiogram.types import FSInputFile
            photo = FSInputFile(default_photo_path)
            return await reply_photo_with_auto_delete(...)
        except Exception:
            # Если не получилось - отправляет без фото
            pass
    
    # Fallback на текст без фото
    sent_message = await message.reply(text, **kwargs)
    ...
```

## Преимущества

1. **Автоматическое добавление фото** - не нужно менять код каждой команды
2. **Graceful fallback** - если фото не загрузится, отправится текст
3. **Гибкость** - можно отключить фото через `use_photo=False`
4. **Единообразие** - все команды выглядят одинаково

## Какие команды теперь с фото

Все команды, которые используют `reply_with_auto_delete()`:

- `/help` - Список команд
- `/me` - Профиль (уже было с фото)
- `/card` - Реквизиты (уже было с фото)
- `/top`, `/topm`, `/topw`, `/topd` - Топы (уже было с фото)
- `/kasa` - Касса команды (уже было с фото)
- `/kurator` - Наставники (уже было с фото)
- `/сервисы` - Сервисы (уже было с фото)
- `/ресурсы` - Материалы (уже было с фото)
- `/сообщество` - Чаты (уже было с фото)
- `/аналитика` - Аналитика (уже было с фото)
- `/идеи` - Идеи (уже было с фото)
- `/инфо` - Информация (уже было с фото)
- `/правила` - Правила (уже было с фото)
- `/поддержка` - Поддержка (уже было с фото)
- `/реф` - Рефералка (уже было с фото)
- `/changetag` - Смена тега
- `/быстро` - Быстрые команды (уже было с фото)
- Все ошибки и уведомления

## Отключение фото для конкретной команды

Если нужно отправить сообщение без фото:

```python
await reply_with_auto_delete(
    message, 
    "Текст без фото",
    use_photo=False  # Отключаем фото
)
```

## Изменение дефолтного фото

Можно указать другое фото:

```python
await reply_with_auto_delete(
    message, 
    "Текст",
    default_photo_path="images/профиль.JPG"  # Другое фото
)
```

## Измененные файлы

- `mainbot/utils/auto_delete.py`

## Результат

✅ Все команды в чате теперь с фото  
✅ Единообразный внешний вид  
✅ Graceful fallback если фото не загрузится  
✅ Обратная совместимость - старый код работает без изменений  
