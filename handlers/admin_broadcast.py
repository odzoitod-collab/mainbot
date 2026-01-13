"""Admin broadcast handlers."""
import logging
import asyncio
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from states.all_states import AdminBroadcastState
from keyboards.admin_kb import get_back_to_admin_keyboard, get_broadcast_confirm_keyboard, get_broadcast_type_keyboard
from database import get_active_user_ids, log_admin_action
from middlewares.admin import admin_only

logger = logging.getLogger(__name__)
router = Router()

URL_PATTERN = re.compile(r'^https?://[^\s]+$', re.IGNORECASE)


@router.callback_query(F.data == "broadcast")
@admin_only
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "📢 <b>РАССЫЛКА</b>\n\nВыберите тип:", reply_markup=get_broadcast_type_keyboard())


@router.callback_query(F.data == "broadcast_text")
@admin_only
async def broadcast_text(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(broadcast_type="text")
    await state.set_state(AdminBroadcastState.waiting_for_title)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "📢 <b>РАССЫЛКА - Шаг 1/4</b>\n\nЗаголовок:")


@router.callback_query(F.data == "broadcast_photo")
@admin_only
async def broadcast_photo(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(broadcast_type="photo")
    await state.set_state(AdminBroadcastState.waiting_for_title)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "📢 <b>РАССЫЛКА С ФОТО - Шаг 1/5</b>\n\nОтправьте фото:")


@router.message(AdminBroadcastState.waiting_for_title, F.photo)
@admin_only
async def receive_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("broadcast_type") == "photo":
        photo_id = message.photo[-1].file_id
        await state.update_data(photo_id=photo_id)
        await message.answer("📢 <b>Шаг 2/5</b>\n\nЗаголовок:")
        return
    await message.answer("❌ Отправьте текст заголовка:")


@router.message(AdminBroadcastState.waiting_for_title)
@admin_only
async def receive_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminBroadcastState.waiting_for_text)
    await message.answer("📢 <b>Шаг 2/4</b>\n\nТекст сообщения:")


@router.message(AdminBroadcastState.waiting_for_text)
@admin_only
async def receive_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text.strip())
    await state.set_state(AdminBroadcastState.waiting_for_button)
    await message.answer(
        "📢 <b>Шаг 3/4</b>\n\n"
        "<b>Кнопка (необязательно):</b>\n\n"
        "<b>🔗 Ссылки:</b>\n"
        "<code>Текст | https://ссылка</code>\n\n"
        "<b>⚡ Специальные команды:</b>\n"
        "<code>Перезапуск | restart</code>\n"
        "<code>Сервисы | services</code>\n"
        "<code>Профиль | profile</code>\n"
        "<code>Помощь | help</code>\n"
        "<code>Топ | top</code>\n"
        "<code>Меню | menu</code>\n\n"
        "Или <code>-</code> чтобы пропустить"
    )


@router.message(AdminBroadcastState.waiting_for_button)
@admin_only
async def receive_button(message: Message, state: FSMContext) -> None:
    btn_text, btn_url, btn_type = None, None, "url"
    
    if message.text.strip() != "-":
        if "|" in message.text:
            parts = message.text.split("|")
            if len(parts) == 2:
                btn_text, btn_action = parts[0].strip(), parts[1].strip()
                
                # Проверяем специальные команды
                if btn_action.lower() in ["restart", "перезапуск", "/restart"]:
                    btn_url = "restart_bot"
                    btn_type = "callback"
                elif btn_action.lower() in ["services", "сервисы", "/services"]:
                    btn_url = "broadcast_services"
                    btn_type = "callback"
                elif btn_action.lower() in ["profile", "профиль", "/me"]:
                    btn_url = "broadcast_profile"
                    btn_type = "callback"
                elif btn_action.lower() in ["help", "помощь", "/help"]:
                    btn_url = "broadcast_help"
                    btn_type = "callback"
                elif btn_action.lower() in ["top", "топ", "/top"]:
                    btn_url = "broadcast_top"
                    btn_type = "callback"
                elif btn_action.lower() in ["menu", "меню", "main_menu"]:
                    btn_url = "main_menu"
                    btn_type = "callback"
                elif URL_PATTERN.match(btn_action):
                    btn_url = btn_action
                    btn_type = "url"
                else:
                    await message.answer(
                        "❌ <b>Неверный формат кнопки!</b>\n\n"
                        "<b>Доступные форматы:</b>\n"
                        "• <code>Текст | https://ссылка</code>\n"
                        "• <code>Перезапуск | restart</code>\n"
                        "• <code>Сервисы | services</code>\n"
                        "• <code>Профиль | profile</code>\n"
                        "• <code>Помощь | help</code>\n"
                        "• <code>Топ | top</code>\n"
                        "• <code>Меню | menu</code>\n\n"
                        "Или <code>-</code> чтобы пропустить"
                    )
                    return
            else:
                await message.answer("❌ Формат: Текст | действие")
                return
        else:
            await message.answer("❌ Формат: Текст | действие")
            return
    
    await state.update_data(button_text=btn_text, button_url=btn_url, button_type=btn_type)
    await state.set_state(AdminBroadcastState.waiting_for_confirm)
    
    data = await state.get_data()
    users = await get_active_user_ids()
    
    preview = f"📢 <b>ПРЕДПРОСМОТР - Шаг 4/4</b>\n\n<b>{data['title']}</b>\n\n{data['text']}\n\n"
    if btn_text:
        if btn_type == "callback":
            action_desc = {
                "restart_bot": "🔄 Перезапуск бота",
                "broadcast_services": "🛠 Открыть сервисы",
                "broadcast_profile": "👤 Открыть профиль",
                "broadcast_help": "❓ Показать помощь",
                "broadcast_top": "🏆 Показать топ",
                "main_menu": "🏠 Главное меню"
            }.get(btn_url, "⚡ Специальная команда")
            preview += f"🔘 {btn_text} ({action_desc})\n\n"
        else:
            preview += f"🔘 {btn_text}\n🔗 {btn_url}\n\n"
    if data.get("photo_id"):
        preview += "🖼 С фото\n\n"
    preview += f"👥 Получателей: {len(users)}\n\nОтправить?"
    
    await message.answer(preview, reply_markup=get_broadcast_confirm_keyboard())


@router.callback_query(F.data == "confirm_broadcast", AdminBroadcastState.waiting_for_confirm)
@admin_only
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Отправка...")
    
    data = await state.get_data()
    await state.clear()
    
    msg_text = f"<b>{data['title']}</b>\n\n{data['text']}"
    keyboard = None
    if data.get('button_text'):
        if data.get('button_type') == 'callback':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=data['button_text'], callback_data=data['button_url'])]
            ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=data['button_text'], url=data['button_url'])]
            ])
    
    users = await get_active_user_ids()
    success, fail, blocked = 0, 0, 0
    photo_id = data.get("photo_id")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"📤 <b>ОТПРАВКА</b>\n\n👥 {len(users)}\n✅ 0\n❌ 0")
    
    for i, user_id in enumerate(users, 1):
        try:
            if photo_id:
                await callback.bot.send_photo(user_id, photo=photo_id, caption=msg_text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await callback.bot.send_message(user_id, msg_text, reply_markup=keyboard, parse_mode="HTML")
            success += 1
            
            if i % 20 == 0:
                try:
                    await edit_with_brand(callback, f"📤 <b>ОТПРАВКА</b>\n\n👥 {len(users)}\n✅ {success}\n❌ {fail}\n🚫 {blocked}\n⏳ {i}/{len(users)}")
                except:
                    pass
            
            await asyncio.sleep(0.05)
        except TelegramForbiddenError:
            blocked += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                if photo_id:
                    await callback.bot.send_photo(user_id, photo=photo_id, caption=msg_text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await callback.bot.send_message(user_id, msg_text, reply_markup=keyboard, parse_mode="HTML")
                success += 1
            except:
                fail += 1
        except:
            fail += 1
    
    await log_admin_action(callback.from_user.id, callback.from_user.username, "broadcast", f"{success}/{len(users)}: {data['title'][:30]}")
    
    pct = (success / len(users) * 100) if users else 0
    await edit_with_brand(callback, f"✅ <b>ГОТОВО!</b>\n\n👥 {len(users)}\n✅ {success}\n❌ {fail}\n🚫 {blocked}\n📊 {pct:.1f}%", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data == "cancel_broadcast", AdminBroadcastState.waiting_for_confirm)
@admin_only
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "❌ Отменено", reply_markup=get_back_to_admin_keyboard())


# ============================================
# ОБРАБОТЧИКИ СПЕЦИАЛЬНЫХ КНОПОК В РАССЫЛКЕ
# ============================================

@router.callback_query(F.data == "restart_bot")
async def handle_restart_bot(callback: CallbackQuery) -> None:
    """Обработчик кнопки перезапуска бота."""
    await callback.answer("🔄 Инициирую перезапуск...", show_alert=True)
    
    # Отправляем сообщение о перезапуске
    await callback.message.edit_text(
        "🔄 <b>БОТ ПЕРЕЗАПУСКАЕТСЯ</b>\n\n"
        "⏳ Подождите 10-30 секунд...\n"
        "🔄 Бот автоматически восстановит работу\n\n"
        "📱 Попробуйте команду /start через минуту"
    )
    
    # Логируем действие
    await log_admin_action(
        callback.from_user.id, 
        callback.from_user.username or callback.from_user.full_name,
        "restart_request", 
        f"Запрос перезапуска через рассылку"
    )
    
    # Используем RestartManager для перезапуска
    try:
        from utils.restart import RestartManager
        restart_manager = RestartManager(callback.bot)
        
        # Запускаем перезапуск в фоне
        asyncio.create_task(restart_manager.request_restart(
            callback.from_user.id, 
            "broadcast_button"
        ))
        
    except Exception as e:
        logger.error(f"Restart error: {e}")
        await callback.message.edit_text(
            "❌ <b>ОШИБКА ПЕРЕЗАПУСКА</b>\n\n"
            "Не удалось перезапустить бота.\n"
            "Обратитесь к техническому администратору."
        )


@router.callback_query(F.data == "broadcast_services")
async def handle_broadcast_services(callback: CallbackQuery) -> None:
    """Обработчик кнопки сервисов в рассылке."""
    await callback.answer()
    
    # Импортируем функцию показа сервисов
    from handlers.user_menu import show_services
    
    # Создаем фейковое сообщение для совместимости
    fake_message = type('obj', (object,), {
        'from_user': callback.from_user,
        'chat': callback.message.chat,
        'bot': callback.bot
    })()
    
    try:
        await show_services(fake_message)
    except Exception as e:
        logger.error(f"Error showing services from broadcast: {e}")
        await callback.message.answer("🛠 <b>СЕРВИСЫ</b>\n\nОткройте меню бота для просмотра сервисов: /start")


@router.callback_query(F.data == "broadcast_profile")
async def handle_broadcast_profile(callback: CallbackQuery) -> None:
    """Обработчик кнопки профиля в рассылке."""
    await callback.answer()
    
    from handlers.user_menu import show_profile
    
    fake_message = type('obj', (object,), {
        'from_user': callback.from_user,
        'chat': callback.message.chat,
        'bot': callback.bot
    })()
    
    try:
        await show_profile(fake_message)
    except Exception as e:
        logger.error(f"Error showing profile from broadcast: {e}")
        await callback.message.answer("👤 <b>ПРОФИЛЬ</b>\n\nОткройте меню бота для просмотра профиля: /me")


@router.callback_query(F.data == "broadcast_help")
async def handle_broadcast_help(callback: CallbackQuery) -> None:
    """Обработчик кнопки помощи в рассылке."""
    await callback.answer()
    
    from handlers.chat_commands import cmd_help
    
    fake_message = type('obj', (object,), {
        'from_user': callback.from_user,
        'chat': callback.message.chat,
        'bot': callback.bot,
        'reply': callback.message.answer,
        'reply_photo': callback.message.answer_photo
    })()
    
    try:
        await cmd_help(fake_message)
    except Exception as e:
        logger.error(f"Error showing help from broadcast: {e}")
        await callback.message.answer(
            "📋 <b>КОМАНДЫ</b>\n\n"
            "👤 /me - Профиль\n"
            "🏆 /top - Топ воркеров\n"
            "🛠 /сервисы - Сервисы\n"
            "🆘 /поддержка - Поддержка\n\n"
            "Полный список: /help"
        )


@router.callback_query(F.data == "broadcast_top")
async def handle_broadcast_top(callback: CallbackQuery) -> None:
    """Обработчик кнопки топа в рассылке."""
    await callback.answer()
    
    from handlers.chat_commands import cmd_top
    
    fake_message = type('obj', (object,), {
        'from_user': callback.from_user,
        'chat': callback.message.chat,
        'bot': callback.bot,
        'reply': callback.message.answer,
        'reply_photo': callback.message.answer_photo
    })()
    
    try:
        await cmd_top(fake_message)
    except Exception as e:
        logger.error(f"Error showing top from broadcast: {e}")
        await callback.message.answer("🏆 <b>ТОП ВОРКЕРОВ</b>\n\nОткройте меню бота для просмотра топа: /top")
