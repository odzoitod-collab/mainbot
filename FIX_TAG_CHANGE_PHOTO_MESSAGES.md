# Исправление работы смены тега с фото-сообщениями

## Проблема

При нажатии кнопки "Сменить тег" из профиля (который содержит фото) возникала ошибка:
```
TelegramBadRequest: there is no text in the message to edit
```

## Причина

Профиль отображается с фото (через `reply_photo_with_auto_delete` или `answer_with_brand` с изображением).
При попытке редактировать такое сообщение через `edit_text()` Telegram возвращает ошибку, 
так как сообщение содержит фото и caption, а не просто text.

## Решение

Добавлена проверка типа сообщения во всех обработчиках смены тега:

```python
if callback.message.photo:
    await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
else:
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
```

## Исправленные обработчики

1. **handle_change_tag_menu** - главное меню смены тега
2. **handle_start_tag_change** - начало ввода нового тега
3. **handle_random_tag** - генерация случайных тегов
4. **handle_select_tag** - выбор сгенерированного тега
5. **handle_back_to_profile** - возврат к профилю

## Изменённые файлы

- `mainbot/handlers/chat_commands.py`

## Результат

✅ Кнопка "Сменить тег" работает из профиля с фото
✅ Все переходы между меню работают корректно
✅ Возврат к профилю работает правильно
✅ Обработка ошибок улучшена

## Дополнительные улучшения

- Добавлено логирование для отладки
- Улучшена обработка исключений
- Добавлены fallback на `callback.answer()` при ошибках редактирования
