"""Mentor panel handlers."""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from keyboards.mentor_kb import (
    get_mentor_panel_keyboard, get_mentor_students_keyboard, get_mentor_broadcast_keyboard,
    get_mentor_channel_keyboard, get_mentor_broadcast_history_keyboard, get_broadcast_detail_keyboard,
    get_broadcast_recipients_keyboard, get_mentor_earnings_keyboard, get_broadcast_confirm_keyboard,
    get_channel_create_keyboard, get_back_to_mentor_panel_keyboard
)
from database import (
    is_user_mentor, get_mentor_data, get_mentor_students, get_mentor_stats,
    get_mentor_channel_info, update_mentor_channel, create_mentor_broadcast,
    get_mentor_broadcasts, get_broadcast_recipients, get_user_mentor_profits
)
from utils.messages import edit_with_brand, answer_with_brand
from utils.design import header
from states.all_states import MentorBroadcastState, MentorChannelState
from config import BRAND_IMAGE_MENTORS

logger = logging.getLogger(__name__)
router = Router()


def _format_date(date_str: str) -> str:
    """Format date for display."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m %H:%M")
    except:
        return date_str[:16] if len(date_str) > 16 else date_str


def _build_mentor_stats_text(stats: dict) -> str:
    """Build mentor statistics text."""
    return (
        f"{header('Статистика наставника', '📊')}\n\n"
        f"👥 <b>Студенты:</b>\n"
        f"├ Всего: {stats.get('total_students', 0)}\n"
        f"└ Активных: {stats.get('active_students', 0)}\n\n"
        f"💰 <b>Доходы:</b>\n"
        f"├ Всего заработано: {stats.get('total_earned', 0):.2f} RUB\n"
        f"├ За этот месяц: {stats.get('this_month_earned', 0):.2f} RUB\n"
        f"├ Средний профит студента: {stats.get('avg_student_profit', 0):.2f} RUB\n"
        f"└ Лучший профит студента: {stats.get('top_student_profit', 0):.2f} RUB"
    )


def _build_students_text(students: list, page: int = 0, per_page: int = 5) -> tuple[str, int]:
    """Build students list text with pagination."""
    if not students:
        return f"{header('Мои студенты', '👥')}\n\n<i>У вас пока нет студентов.</i>", 1
    
    total_pages = max(1, -(-len(students) // per_page))
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    page_students = students[start:start + per_page]
    
    text = f"{header('Мои студенты', '👥')}\n\n"
    text += f"<i>Стр. {page + 1}/{total_pages} • Всего: {len(students)}</i>\n\n"
    
    for i, student in enumerate(page_students, start + 1):
        tag = student.get('student_tag', '#irl_???')
        profit = student.get('total_profit', 0)
        earnings = student.get('mentor_earnings', 0)
        last_activity = student.get('last_activity')
        
        activity_text = "🟢 Активен"
        if last_activity:
            try:
                last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                delta = datetime.now(timezone.utc) - last_activity_dt
                if delta.days >= 7:
                    activity_text = "🔴 Неактивен"
            except Exception:
                activity_text = "⚪ Неизвестно"
        else:
            activity_text = "🔴 Неактивен"
        
        text += (
            f"{i}. <b>{tag}</b>\n"
            f"   💰 Профит: {profit:.2f} RUB\n"
            f"   💵 Ваш доход: {earnings:.2f} RUB\n"
            f"   📊 {activity_text}\n\n"
        )
    
    return text, total_pages


def _build_broadcast_history_text(broadcasts: list, page: int = 0, per_page: int = 3) -> tuple[str, int]:
    """Build broadcast history text."""
    if not broadcasts:
        return f"{header('История рассылок', '📈')}\n\n<i>Рассылок пока не было.</i>", 1
    
    total_pages = max(1, -(-len(broadcasts) // per_page))
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    page_broadcasts = broadcasts[start:start + per_page]
    
    text = f"{header('История рассылок', '📈')}\n\n"
    text += f"<i>Стр. {page + 1}/{total_pages} • Всего: {len(broadcasts)}</i>\n\n"
    
    for broadcast in page_broadcasts:
        status_emoji = {
            'pending': '⏳',
            'sending': '📤',
            'completed': '✅',
            'failed': '❌'
        }.get(broadcast['status'], '❓')
        
        message_preview = broadcast['message_text'][:50] + "..." if len(broadcast['message_text']) > 50 else broadcast['message_text']
        
        text += (
            f"{status_emoji} <b>Рассылка #{broadcast['id']}</b>\n"
            f"📝 {message_preview}\n"
            f"👥 {broadcast['sent_count']}/{broadcast['total_count']}\n"
            f"📅 {_format_date(broadcast['created_at'])}\n\n"
        )
    
    return text, total_pages


@router.callback_query(F.data == "mentor_panel")
async def show_mentor_panel(callback: CallbackQuery) -> None:
    """Show mentor panel main menu."""
    await callback.answer()
    
    # Check if user is mentor
    if not await is_user_mentor(callback.from_user.id):
        await callback.answer("❌ Вы не являетесь наставником", show_alert=True)
        return
    
    # Load mentor data
    data = await get_mentor_data(callback.from_user.id)
    stats = data.get('stats', {})
    
    text = (
        f"{header('Панель наставника', '👨‍🏫')}\n\n"
        f"👋 Добро пожаловать в панель наставника!\n\n"
        f"📊 <b>Краткая статистика:</b>\n"
        f"├ Студентов: {stats.get('total_students', 0)}\n"
        f"├ Активных: {stats.get('active_students', 0)}\n"
        f"└ Заработано: {stats.get('total_earned', 0):.2f} RUB\n\n"
        f"Выберите действие:"
    )
    
    await edit_with_brand(
        callback, text, 
        reply_markup=get_mentor_panel_keyboard(),
        image_path=BRAND_IMAGE_MENTORS
    )


@router.callback_query(F.data == "mentor_stats")
async def show_mentor_stats(callback: CallbackQuery) -> None:
    """Show detailed mentor statistics."""
    await callback.answer()
    
    stats = await get_mentor_stats(callback.from_user.id)
    text = _build_mentor_stats_text(stats)
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_back_to_mentor_panel_keyboard(),
        image_path=BRAND_IMAGE_MENTORS
    )


@router.callback_query(F.data == "mentor_students")
@router.callback_query(F.data.startswith("mentor_students_page_"))
async def show_mentor_students(callback: CallbackQuery) -> None:
    """Show mentor students list."""
    await callback.answer()
    
    logger.info(f"User {callback.from_user.id} viewing mentor students")
    
    # Get page number
    page = 0
    if callback.data.startswith("mentor_students_page_"):
        try:
            page = int(callback.data.split("_")[-1])
            logger.info(f"Page: {page}")
        except (IndexError, ValueError):
            page = 0
    
    try:
        students = await get_mentor_students(callback.from_user.id)
        logger.info(f"Found {len(students)} students for mentor {callback.from_user.id}")
        
        text, total_pages = _build_students_text(students, page)
        
        # Проверяем что текст не пустой
        if not text or not text.strip():
            text = "❌ Нет данных для отображения"
            logger.warning(f"Empty text generated for mentor {callback.from_user.id}")
        
        await edit_with_brand(
            callback, text,
            reply_markup=get_mentor_students_keyboard(page, total_pages),
            image_path=BRAND_IMAGE_MENTORS
        )
    except Exception as e:
        logger.error(f"Error showing mentor students: {e}", exc_info=True)
        try:
            await callback.message.edit_text(
                "❌ Ошибка загрузки списка студентов.\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_back_to_mentor_panel_keyboard()
            )
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}", exc_info=True)
            await callback.answer("❌ Ошибка загрузки списка студентов", show_alert=True)


@router.callback_query(F.data == "mentor_broadcast")
async def show_mentor_broadcast_menu(callback: CallbackQuery) -> None:
    """Show mentor broadcast menu."""
    await callback.answer()
    
    text = (
        f"{header('Рассылка студентам', '📢')}\n\n"
        f"📝 Выберите тип рассылки:\n\n"
        f"• <b>Текстовая</b> - обычное сообщение\n"
        f"• <b>С изображением</b> - сообщение с картинкой\n\n"
        f"⚠️ Рассылка будет отправлена всем вашим студентам"
    )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_mentor_broadcast_keyboard(),
        image_path=BRAND_IMAGE_MENTORS
    )


@router.callback_query(F.data == "mentor_broadcast_text")
async def start_text_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Start text broadcast creation."""
    await callback.answer()
    
    text = (
        f"{header('Текстовая рассылка', '📝')}\n\n"
        f"Отправьте текст сообщения для рассылки:\n\n"
        f"💡 <b>Советы:</b>\n"
        f"• Используйте HTML разметку\n"
        f"• Максимум 4096 символов\n"
        f"• Будьте вежливы со студентами"
    )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_back_to_mentor_panel_keyboard()
    )
    
    await state.set_state(MentorBroadcastState.waiting_for_message)
    await state.update_data(broadcast_type="text")


@router.callback_query(F.data == "mentor_broadcast_photo")
async def start_photo_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Start photo broadcast creation."""
    await callback.answer()
    
    text = (
        f"{header('Рассылка с изображением', '🖼')}\n\n"
        f"Отправьте изображение с подписью:\n\n"
        f"💡 <b>Советы:</b>\n"
        f"• Подпись до 1024 символов\n"
        f"• Используйте качественные изображения\n"
        f"• Подпись может содержать HTML разметку"
    )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_back_to_mentor_panel_keyboard()
    )
    
    await state.set_state(MentorBroadcastState.waiting_for_photo)
    await state.update_data(broadcast_type="photo")


@router.message(MentorBroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    """Process broadcast message."""
    if not message.text:
        await message.reply("❌ Отправьте текстовое сообщение.")
        return
    
    if len(message.text) > 4096:
        await message.reply("❌ Сообщение слишком длинное (максимум 4096 символов).")
        return
    
    # Get students count
    students = await get_mentor_students(message.from_user.id)
    students_count = len(students)
    
    text = (
        f"{header('Подтверждение рассылки', '✅')}\n\n"
        f"📝 <b>Ваше сообщение:</b>\n"
        f"{message.text}\n\n"
        f"👥 <b>Получатели:</b> {students_count} студентов\n\n"
        f"Отправить рассылку?"
    )
    
    await state.update_data(
        message_text=message.text,
        students_count=students_count
    )
    
    await message.reply(text, reply_markup=get_broadcast_confirm_keyboard())
    await state.set_state(MentorBroadcastState.waiting_for_confirm)


@router.message(MentorBroadcastState.waiting_for_photo)
async def process_broadcast_photo(message: Message, state: FSMContext) -> None:
    """Process broadcast photo."""
    if not message.photo:
        await message.reply("❌ Отправьте изображение с подписью.")
        return
    
    caption = message.caption or ""
    if len(caption) > 1024:
        await message.reply("❌ Подпись слишком длинная (максимум 1024 символа).")
        return
    
    # Get students count
    students = await get_mentor_students(message.from_user.id)
    students_count = len(students)
    
    text = (
        f"{header('Подтверждение рассылки', '✅')}\n\n"
        f"🖼 <b>Изображение с подписью:</b>\n"
        f"{caption}\n\n"
        f"👥 <b>Получатели:</b> {students_count} студентов\n\n"
        f"Отправить рассылку?"
    )
    
    await state.update_data(
        message_text=caption,
        media_file_id=message.photo[-1].file_id,
        students_count=students_count
    )
    
    await message.reply(text, reply_markup=get_broadcast_confirm_keyboard())
    await state.set_state(MentorBroadcastState.waiting_for_confirm)


@router.callback_query(F.data == "mentor_broadcast_confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Confirm and create broadcast."""
    await callback.answer()
    
    data = await state.get_data()
    broadcast_type = data.get('broadcast_type', 'text')
    message_text = data.get('message_text', '')
    media_file_id = data.get('media_file_id')
    
    # Create broadcast
    broadcast_id = await create_mentor_broadcast(
        callback.from_user.id,
        message_text,
        broadcast_type,
        media_file_id
    )
    
    if broadcast_id:
        text = (
            f"✅ <b>РАССЫЛКА СОЗДАНА</b>\n\n"
            f"📢 Рассылка #{broadcast_id} добавлена в очередь\n"
            f"👥 Будет отправлена {data.get('students_count', 0)} студентам\n\n"
            f"📊 Следите за статусом в истории рассылок"
        )
    else:
        text = "❌ Ошибка создания рассылки. Попробуйте позже."
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_back_to_mentor_panel_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data == "mentor_broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel broadcast creation."""
    await callback.answer()
    await state.clear()
    await show_mentor_broadcast_menu(callback)


@router.callback_query(F.data == "mentor_broadcast_history")
@router.callback_query(F.data.startswith("mentor_broadcast_history_page_"))
async def show_broadcast_history(callback: CallbackQuery) -> None:
    """Show mentor broadcast history."""
    await callback.answer()
    
    # Get page number
    page = 0
    if callback.data.startswith("mentor_broadcast_history_page_"):
        try:
            page = int(callback.data.split("_")[-1])
        except (IndexError, ValueError):
            page = 0
    
    broadcasts = await get_mentor_broadcasts(callback.from_user.id, 20)
    text, total_pages = _build_broadcast_history_text(broadcasts, page)
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_mentor_broadcast_history_keyboard(page, total_pages),
        image_path=BRAND_IMAGE_MENTORS
    )


@router.callback_query(F.data == "mentor_channel")
async def show_mentor_channel(callback: CallbackQuery) -> None:
    """Show mentor channel management."""
    await callback.answer()
    
    channel_info = await get_mentor_channel_info(callback.from_user.id)
    has_channel = channel_info is not None and channel_info.get('telegram_channel')
    
    if has_channel:
        text = (
            f"{header('Мой ТГК', '📺')}\n\n"
            f"📺 <b>Название:</b> {channel_info.get('telegram_channel', 'Не указано')}\n"
            f"📝 <b>Описание:</b> {channel_info.get('channel_description', 'Не указано')}\n"
            f"🔗 <b>Ссылка:</b> {channel_info.get('channel_invite_link', 'Не указана')}\n\n"
            f"💡 Ваши студенты видят ссылку на ТГК в профиле наставника"
        )
    else:
        text = (
            f"{header('Создание ТГК', '📺')}\n\n"
            f"📺 У вас пока нет Telegram канала\n\n"
            f"💡 <b>Преимущества ТГК:</b>\n"
            f"• Прямая связь со студентами\n"
            f"• Дополнительные материалы\n"
            f"• Повышение авторитета\n"
            f"• Студенты видят ссылку в профиле\n\n"
            f"Создать канал?"
        )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_mentor_channel_keyboard(has_channel),
        image_path=BRAND_IMAGE_MENTORS
    )


@router.callback_query(F.data == "mentor_channel_create")
async def start_channel_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Start channel creation process."""
    await callback.answer()
    
    text = (
        f"{header('Создание ТГК', '📺')}\n\n"
        f"📝 <b>Шаг 1 из 3: Название канала</b>\n\n"
        f"Введите название вашего Telegram канала:\n\n"
        f"💡 <b>Примеры:</b>\n"
        f"• Арбитраж с Иваном\n"
        f"• Крипто Мастер\n"
        f"• Профит Гуру"
    )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_channel_create_keyboard()
    )
    
    await state.set_state(MentorChannelState.waiting_for_channel_name)


@router.message(MentorChannelState.waiting_for_channel_name)
async def process_channel_name(message: Message, state: FSMContext) -> None:
    """Process channel name."""
    if not message.text or len(message.text) > 100:
        await message.reply("❌ Название должно быть от 1 до 100 символов.")
        return
    
    await state.update_data(channel_name=message.text)
    
    text = (
        f"{header('Создание ТГК', '📺')}\n\n"
        f"📝 <b>Шаг 2 из 3: Описание канала</b>\n\n"
        f"Введите описание вашего канала:\n\n"
        f"💡 <b>Что писать:</b>\n"
        f"• О чем ваш канал\n"
        f"• Какую пользу получат подписчики\n"
        f"• Ваш опыт и достижения"
    )
    
    await message.reply(text)
    await state.set_state(MentorChannelState.waiting_for_channel_description)


@router.message(MentorChannelState.waiting_for_channel_description)
async def process_channel_description(message: Message, state: FSMContext) -> None:
    """Process channel description."""
    if not message.text or len(message.text) > 500:
        await message.reply("❌ Описание должно быть от 1 до 500 символов.")
        return
    
    await state.update_data(channel_description=message.text)
    
    text = (
        f"{header('Создание ТГК', '📺')}\n\n"
        f"📝 <b>Шаг 3 из 3: Ссылка на канал</b>\n\n"
        f"Отправьте ссылку на ваш Telegram канал:\n\n"
        f"💡 <b>Формат:</b>\n"
        f"• https://t.me/your_channel\n"
        f"• @your_channel\n\n"
        f"⚠️ Канал должен быть публичным"
    )
    
    await message.reply(text)
    await state.set_state(MentorChannelState.waiting_for_channel_link)


@router.message(MentorChannelState.waiting_for_channel_link)
async def process_channel_link(message: Message, state: FSMContext) -> None:
    """Process channel link."""
    if not message.text:
        await message.reply("❌ Отправьте ссылку на канал.")
        return
    
    link = message.text.strip()
    
    # Basic validation
    if not (link.startswith('https://t.me/') or link.startswith('@')):
        await message.reply("❌ Неверный формат ссылки. Используйте https://t.me/канал или @канал")
        return
    
    data = await state.get_data()
    
    # Save channel info
    success = await update_mentor_channel(
        message.from_user.id,
        data['channel_name'],
        data['channel_description'],
        link
    )
    
    if success:
        text = (
            f"✅ <b>ТГК СОЗДАН</b>\n\n"
            f"📺 <b>Название:</b> {data['channel_name']}\n"
            f"📝 <b>Описание:</b> {data['channel_description']}\n"
            f"🔗 <b>Ссылка:</b> {link}\n\n"
            f"🎉 Теперь ваши студенты увидят ссылку на канал!"
        )
    else:
        text = "❌ Ошибка сохранения канала. Попробуйте позже."
    
    await message.reply(text, reply_markup=get_back_to_mentor_panel_keyboard())
    await state.clear()


@router.callback_query(F.data == "mentor_earnings")
@router.callback_query(F.data.startswith("mentor_earnings_page_"))
async def show_mentor_earnings(callback: CallbackQuery) -> None:
    """Show mentor earnings history."""
    await callback.answer()
    
    # Get page number
    page = 0
    if callback.data.startswith("mentor_earnings_page_"):
        try:
            page = int(callback.data.split("_")[-1])
        except (IndexError, ValueError):
            page = 0
    
    earnings = await get_user_mentor_profits(callback.from_user.id)
    
    if not earnings:
        text = f"{header('Мои доходы', '💰')}\n\n<i>Доходов пока нет.</i>"
        total_pages = 1
    else:
        per_page = 5
        total_pages = max(1, -(-len(earnings) // per_page))
        page = max(0, min(page, total_pages - 1))
        start = page * per_page
        page_earnings = earnings[start:start + per_page]
        
        text = f"{header('Мои доходы', '💰')}\n\n"
        text += f"<i>Стр. {page + 1}/{total_pages} • Всего: {len(earnings)}</i>\n\n"
        
        for earning in page_earnings:
            student_name = earning.get('student', {}).get('full_name', 'Неизвестный')
            status_emoji = "✅" if earning['status'] == 'paid' else "⏳"
            
            text += (
                f"{status_emoji} <b>{earning['amount']:.2f} RUB</b>\n"
                f"👤 От: {student_name}\n"
                f"📊 {earning['percent']}% от профита\n"
                f"📅 {_format_date(earning['created_at'])}\n\n"
            )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_mentor_earnings_keyboard(page, total_pages),
        image_path=BRAND_IMAGE_MENTORS
    )