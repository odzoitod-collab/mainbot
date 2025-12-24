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
    await message.answer("📢 <b>Шаг 3/4</b>\n\nКнопка: <code>Текст | https://...</code>\n\nИли <code>-</code> чтобы пропустить")


@router.message(AdminBroadcastState.waiting_for_button)
@admin_only
async def receive_button(message: Message, state: FSMContext) -> None:
    btn_text, btn_url = None, None
    
    if message.text.strip() != "-":
        if "|" in message.text:
            parts = message.text.split("|")
            if len(parts) == 2:
                btn_text, btn_url = parts[0].strip(), parts[1].strip()
                if not URL_PATTERN.match(btn_url):
                    await message.answer("❌ Неверная ссылка:")
                    return
            else:
                await message.answer("❌ Формат: Текст | https://...")
                return
        else:
            await message.answer("❌ Формат: Текст | https://...")
            return
    
    await state.update_data(button_text=btn_text, button_url=btn_url)
    await state.set_state(AdminBroadcastState.waiting_for_confirm)
    
    data = await state.get_data()
    users = await get_active_user_ids()
    
    preview = f"📢 <b>ПРЕДПРОСМОТР - Шаг 4/4</b>\n\n<b>{data['title']}</b>\n\n{data['text']}\n\n"
    if btn_text:
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
                await callback.bot.send_photo(user_id, photo=photo_id, caption=msg_text, reply_markup=keyboard)
            else:
                await callback.bot.send_message(user_id, msg_text, reply_markup=keyboard)
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
                    await callback.bot.send_photo(user_id, photo=photo_id, caption=msg_text, reply_markup=keyboard)
                else:
                    await callback.bot.send_message(user_id, msg_text, reply_markup=keyboard)
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
