"""Community creation handlers."""
import logging
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.all_states import CommunityCreateState
from database import create_community_request, get_user_stats
from keyboards.user_kb import get_community_create_keyboard, get_back_to_menu_keyboard
from utils.messages import answer_with_brand, edit_with_brand
from utils.design import header
from config import BRAND_IMAGE_COMMUNITY, ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()


def is_valid_telegram_link(link: str) -> bool:
    """Check if link is valid Telegram chat link."""
    patterns = [
        r'^https://t\.me/[a-zA-Z0-9_]+$',
        r'^https://t\.me/joinchat/[a-zA-Z0-9_-]+$',
        r'^https://t\.me/\+[a-zA-Z0-9_-]+$'
    ]
    return any(re.match(pattern, link) for pattern in patterns)


@router.message(CommunityCreateState.waiting_for_name)
async def process_community_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    
    if len(name) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
        return
    
    if len(name) < 3:
        await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
        return
    
    await state.update_data(name=name)
    
    text = (
        f"{header('Создание комьюнити', '➕')}\n\n"
        f"🎯 <b>Шаг 2 из 3: Описание</b>\n\n"
        f"📝 <b>Название:</b> {name}\n\n"
        f"Введите описание комьюнити:\n"
        f"<i>Расскажите, чем занимается ваше сообщество</i>"
    )
    
    await answer_with_brand(
        message, text,
        reply_markup=get_community_create_keyboard(),
        image_path=BRAND_IMAGE_COMMUNITY
    )
    await state.set_state(CommunityCreateState.waiting_for_description)


@router.message(CommunityCreateState.waiting_for_description)
async def process_community_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()
    
    if len(description) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов.")
        return
    
    if len(description) < 10:
        await message.answer("❌ Описание слишком короткое. Минимум 10 символов.")
        return
    
    await state.update_data(description=description)
    
    text = (
        f"{header('Создание комьюнити', '➕')}\n\n"
        f"🎯 <b>Шаг 3 из 3: Ссылка на чат</b>\n\n"
        f"Введите ссылку на Telegram чат/канал:\n\n"
        f"<b>Примеры правильных ссылок:</b>\n"
        f"• https://t.me/your_channel\n"
        f"• https://t.me/joinchat/ABC123\n"
        f"• https://t.me/+ABC123\n\n"
        f"<i>Убедитесь, что ссылка рабочая!</i>"
    )
    
    await answer_with_brand(
        message, text,
        reply_markup=get_community_create_keyboard(),
        image_path=BRAND_IMAGE_COMMUNITY
    )
    await state.set_state(CommunityCreateState.waiting_for_chat_link)


@router.message(CommunityCreateState.waiting_for_chat_link)
async def process_community_chat_link(message: Message, state: FSMContext) -> None:
    chat_link = message.text.strip()
    
    if not is_valid_telegram_link(chat_link):
        await message.answer(
            "❌ Неправильная ссылка. Используйте ссылки вида:\n"
            "• https://t.me/your_channel\n"
            "• https://t.me/joinchat/ABC123\n"
            "• https://t.me/+ABC123"
        )
        return
    
    await state.update_data(chat_link=chat_link)
    data = await state.get_data()
    
    text = (
        f"{header('Подтверждение создания', '✅')}\n\n"
        f"📝 <b>Название:</b> {data['name']}\n"
        f"📄 <b>Описание:</b> {data['description']}\n"
        f"💬 <b>Ссылка:</b> {data['chat_link']}\n\n"
        f"⚠️ <b>Важно:</b>\n"
        f"• Комьюнити будет отправлено на модерацию\n"
        f"• После одобрения админом оно появится в списке\n"
        f"• Убедитесь, что все данные корректны\n\n"
        f"Подтвердить создание?"
    )
    
    keyboard = [
        [
            {"text": "✅ Создать", "callback_data": "community_confirm_create"},
            {"text": "❌ Отмена", "callback_data": "community"}
        ]
    ]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Создать", callback_data="community_confirm_create")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="community")]
    ])
    
    await answer_with_brand(
        message, text,
        reply_markup=reply_markup,
        image_path=BRAND_IMAGE_COMMUNITY
    )
    await state.set_state(CommunityCreateState.waiting_for_confirm)


@router.callback_query(F.data == "community_confirm_create", CommunityCreateState.waiting_for_confirm)
async def confirm_community_creation(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    data = await state.get_data()
    
    try:
        community_id = await create_community_request(
            callback.from_user.id,
            data['name'],
            data['description'],
            data['chat_link']
        )
        
        if community_id:
            text = (
                f"✅ <b>Заявка отправлена!</b>\n\n"
                f"📝 <b>Комьюнити:</b> {data['name']}\n\n"
                f"⏳ Ваша заявка отправлена на модерацию.\n"
                f"После одобрения администратором комьюнити\n"
                f"появится в общем списке.\n\n"
                f"📬 Вы получите уведомление о результате."
            )
            
            # Notify admins
            admin_text = (
                f"🆕 <b>Новая заявка на комьюнити</b>\n\n"
                f"👤 <b>От:</b> {callback.from_user.full_name}\n"
                f"🆔 <b>ID:</b> <code>{callback.from_user.id}</code>\n"
                f"📝 <b>Название:</b> {data['name']}\n"
                f"📄 <b>Описание:</b> {data['description']}\n"
                f"💬 <b>Ссылка:</b> {data['chat_link']}\n\n"
                f"Проверьте в админ панели для одобрения."
            )
            
            # Send to all admins
            from aiogram import Bot
            bot = callback.bot
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, admin_text)
                except:
                    pass
            
        else:
            text = "❌ Ошибка при создании заявки. Попробуйте позже."
        
    except Exception as e:
        logger.error(f"Error creating community: {e}")
        text = "❌ Ошибка при создании заявки. Попробуйте позже."
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_back_to_menu_keyboard(),
        image_path=BRAND_IMAGE_COMMUNITY
    )
    await state.clear()