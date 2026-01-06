"""Admin community management handlers."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import (
    get_pending_communities, get_community, approve_community, 
    reject_community, delete_community, get_communities_for_user,
    log_admin_action, create_notification
)
from keyboards.admin_kb import (
    get_communities_admin_keyboard, get_pending_communities_keyboard,
    get_community_review_keyboard, get_all_communities_keyboard,
    get_back_to_admin_keyboard
)
from utils.messages import edit_with_brand
from utils.design import header
from config import ADMIN_IDS, BRAND_IMAGE_COMMUNITY

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "manage_communities")
async def show_communities_management(callback: CallbackQuery) -> None:
    """Show communities management menu."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    text = (
        f"{header('Управление комьюнити', '👥')}\n\n"
        f"🛠 <b>Административная панель</b>\n\n"
        f"Здесь вы можете:\n"
        f"• Модерировать заявки на создание\n"
        f"• Просматривать все комьюнити\n"
        f"• Удалять комьюнити при необходимости"
    )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_communities_admin_keyboard(),
        image_path=BRAND_IMAGE_COMMUNITY
    )


@router.callback_query(F.data == "pending_communities")
async def show_pending_communities(callback: CallbackQuery) -> None:
    """Show pending communities for review."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    communities = await get_pending_communities()
    
    text = (
        f"{header('Заявки на модерацию', '⏳')}\n\n"
        f"📋 <b>Ожидают рассмотрения: {len(communities)}</b>\n\n"
    )
    
    if communities:
        text += "Выберите заявку для рассмотрения:"
    else:
        text += "✅ Все заявки рассмотрены!"
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_pending_communities_keyboard(communities),
        image_path=BRAND_IMAGE_COMMUNITY
    )


@router.callback_query(F.data.startswith("review_community_"))
async def review_community(callback: CallbackQuery) -> None:
    """Review specific community."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    try:
        community_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    community = await get_community(community_id)
    if not community:
        await callback.answer("❌ Комьюнити не найдено", show_alert=True)
        return
    
    creator_info = community.get('creator', {})
    creator_name = creator_info.get('full_name', 'Неизвестный')
    creator_username = f"@{creator_info.get('username')}" if creator_info.get('username') else "Нет username"
    
    text = (
        f"{header('Модерация комьюнити', '📝')}\n\n"
        f"📝 <b>Название:</b> {community['name']}\n\n"
        f"📄 <b>Описание:</b>\n{community.get('description', 'Нет описания')}\n\n"
        f"💬 <b>Ссылка на чат:</b>\n{community['chat_link']}\n\n"
        f"👤 <b>Создатель:</b> {creator_name}\n"
        f"🆔 <b>Username:</b> {creator_username}\n"
        f"🆔 <b>ID:</b> <code>{community['creator_id']}</code>\n\n"
        f"📅 <b>Дата заявки:</b> {community['created_at'][:16]}\n\n"
        f"❓ <b>Одобрить или отклонить заявку?</b>"
    )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_community_review_keyboard(community_id),
        image_path=BRAND_IMAGE_COMMUNITY
    )


@router.callback_query(F.data.startswith("approve_community_"))
async def approve_community_handler(callback: CallbackQuery) -> None:
    """Approve community."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    try:
        community_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    community = await get_community(community_id)
    if not community:
        await callback.answer("❌ Комьюнити не найдено", show_alert=True)
        return
    
    success = await approve_community(community_id, callback.from_user.id)
    
    if success:
        # Log admin action
        await log_admin_action(
            callback.from_user.id,
            callback.from_user.username or callback.from_user.full_name,
            "approve_community",
            f"Одобрено комьюнити: {community['name']}",
            community['creator_id']
        )
        
        # Notify creator
        await create_notification(
            community['creator_id'],
            "community_approved",
            "Комьюнити одобрено! 🎉",
            f"Ваше комьюнити '{community['name']}' было одобрено и теперь доступно всем пользователям!"
        )
        
        # Notify creator via bot message
        try:
            await callback.bot.send_message(
                community['creator_id'],
                f"🎉 <b>Отличные новости!</b>\n\n"
                f"Ваше комьюнити <b>'{community['name']}'</b> было одобрено администратором!\n\n"
                f"Теперь оно доступно всем пользователям в разделе 'Комьюнити'.\n"
                f"Желаем успехов в развитии сообщества! 🚀"
            )
        except:
            pass
        
        text = (
            f"✅ <b>Комьюнити одобрено!</b>\n\n"
            f"📝 <b>Название:</b> {community['name']}\n"
            f"👤 <b>Создатель:</b> {community.get('creator', {}).get('full_name', 'Неизвестный')}\n\n"
            f"Комьюнити теперь доступно всем пользователям.\n"
            f"Создатель получил уведомление об одобрении."
        )
        
        await edit_with_brand(
            callback, text,
            reply_markup=get_back_to_admin_keyboard(),
            image_path=BRAND_IMAGE_COMMUNITY
        )
    else:
        await callback.answer("❌ Ошибка при одобрении", show_alert=True)


@router.callback_query(F.data.startswith("reject_community_"))
async def reject_community_handler(callback: CallbackQuery) -> None:
    """Reject community."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    try:
        community_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    community = await get_community(community_id)
    if not community:
        await callback.answer("❌ Комьюнити не найдено", show_alert=True)
        return
    
    success = await reject_community(community_id, callback.from_user.id)
    
    if success:
        # Log admin action
        await log_admin_action(
            callback.from_user.id,
            callback.from_user.username or callback.from_user.full_name,
            "reject_community",
            f"Отклонено комьюнити: {community['name']}",
            community['creator_id']
        )
        
        # Notify creator
        await create_notification(
            community['creator_id'],
            "community_rejected",
            "Комьюнити отклонено",
            f"К сожалению, ваше комьюнити '{community['name']}' не прошло модерацию."
        )
        
        # Notify creator via bot message
        try:
            await callback.bot.send_message(
                community['creator_id'],
                f"❌ <b>Заявка отклонена</b>\n\n"
                f"К сожалению, ваше комьюнити <b>'{community['name']}'</b> не прошло модерацию.\n\n"
                f"Возможные причины:\n"
                f"• Неподходящий контент\n"
                f"• Нерабочая ссылка на чат\n"
                f"• Нарушение правил сообщества\n\n"
                f"Вы можете создать новую заявку с исправлениями."
            )
        except:
            pass
        
        text = (
            f"❌ <b>Комьюнити отклонено</b>\n\n"
            f"📝 <b>Название:</b> {community['name']}\n"
            f"👤 <b>Создатель:</b> {community.get('creator', {}).get('full_name', 'Неизвестный')}\n\n"
            f"Заявка отклонена.\n"
            f"Создатель получил уведомление об отклонении."
        )
        
        await edit_with_brand(
            callback, text,
            reply_markup=get_back_to_admin_keyboard(),
            image_path=BRAND_IMAGE_COMMUNITY
        )
    else:
        await callback.answer("❌ Ошибка при отклонении", show_alert=True)


@router.callback_query(F.data == "all_communities")
async def show_all_communities(callback: CallbackQuery) -> None:
    """Show all approved communities for deletion."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    # Get all approved communities
    communities = await get_communities_for_user(0)  # Get all communities
    approved_communities = [c for c in communities if c.get('status') == 'approved']
    
    text = (
        f"{header('Все комьюнити', '📋')}\n\n"
        f"📊 <b>Всего активных: {len(approved_communities)}</b>\n\n"
    )
    
    if approved_communities:
        text += "Выберите комьюнити для удаления:"
    else:
        text += "📭 Нет активных комьюнити"
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_all_communities_keyboard(approved_communities),
        image_path=BRAND_IMAGE_COMMUNITY
    )


@router.callback_query(F.data.startswith("delete_community_"))
async def delete_community_handler(callback: CallbackQuery) -> None:
    """Delete community."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    try:
        community_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    community = await get_community(community_id)
    if not community:
        await callback.answer("❌ Комьюнити не найдено", show_alert=True)
        return
    
    success = await delete_community(community_id)
    
    if success:
        # Log admin action
        await log_admin_action(
            callback.from_user.id,
            callback.from_user.username or callback.from_user.full_name,
            "delete_community",
            f"Удалено комьюнити: {community['name']}",
            community['creator_id']
        )
        
        # Notify creator
        await create_notification(
            community['creator_id'],
            "community_deleted",
            "Комьюнити удалено",
            f"Ваше комьюнити '{community['name']}' было удалено администратором."
        )
        
        text = (
            f"🗑 <b>Комьюнити удалено</b>\n\n"
            f"📝 <b>Название:</b> {community['name']}\n"
            f"👤 <b>Создатель:</b> {community.get('creator', {}).get('full_name', 'Неизвестный')}\n"
            f"👥 <b>Участников было:</b> {community.get('members_count', 0)}\n\n"
            f"Комьюнити успешно удалено из системы."
        )
        
        await edit_with_brand(
            callback, text,
            reply_markup=get_back_to_admin_keyboard(),
            image_path=BRAND_IMAGE_COMMUNITY
        )
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)