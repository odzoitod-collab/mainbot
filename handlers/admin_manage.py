"""Admin management handlers for payouts, content, users and stats."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.all_states import AdminContentState
from keyboards.admin_kb import (
    get_back_to_admin_keyboard, get_payout_keyboard, get_content_category_keyboard,
    get_content_action_keyboard, get_service_list_keyboard, get_resource_list_keyboard,
    get_resource_type_keyboard, get_users_management_keyboard, get_user_action_keyboard,
    get_user_list_keyboard, get_stats_keyboard, get_payout_type_keyboard,
    get_referral_payout_keyboard, get_mentor_payout_keyboard
)
from database import (
    get_unpaid_summary, mark_profits_paid, get_user, add_service, delete_service,
    get_services, add_resource, delete_resource, get_resources, log_admin_action,
    get_unpaid_referral_summary, mark_referral_profits_paid,
    get_unpaid_mentor_summary, mark_mentor_profits_paid,
    get_users_by_status, get_team_stats_by_period, ban_user, unban_user,
    get_user_by_username, get_user_profits
)
from middlewares.admin import admin_only

logger = logging.getLogger(__name__)
router = Router()


# ============================================
# PAYOUTS
# ============================================

@router.callback_query(F.data == "view_payouts")
@admin_only
async def show_payouts(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "💸 <b>ВЫПЛАТЫ</b>\n\nВыберите тип:", reply_markup=get_payout_type_keyboard())


@router.callback_query(F.data == "payouts_workers")
@admin_only
async def show_worker_payouts(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    
    summary = await get_unpaid_summary()
    if not summary:
        await edit_with_brand(callback, "💸 <b>ВЫПЛАТЫ ВОРКЕРАМ</b>\n\nНет ожидающих.", reply_markup=get_back_to_admin_keyboard())
        return

    total = sum(item['total_unpaid'] for item in summary)
    lines = [f"💸 <b>ОЖИДАЮЩИЕ ВЫПЛАТЫ ВОРКЕРАМ</b>\n\n💰 Всего: {total:.2f} RUB\n"]
    for item in summary[:10]:
        # Показываем тег вместо имени
        display_name = item.get('user_tag', f"@{item['username']}" if item['username'] else item['full_name'])
        lines.append(f"🏷 {display_name} • {item['total_unpaid']:.0f} ₽ ({item['count']})")
    
    await edit_with_brand(callback, "\n".join(lines), reply_markup=get_payout_keyboard(summary))


@router.callback_query(F.data == "payouts_referrals")
@admin_only
async def show_referral_payouts(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    
    summary = await get_unpaid_referral_summary()
    if not summary:
        await edit_with_brand(callback, "🔗 <b>РЕФЕРАЛЬНЫЕ ВЫПЛАТЫ</b>\n\nНет ожидающих.", reply_markup=get_back_to_admin_keyboard())
        return
    
    total = sum(item['total_unpaid'] for item in summary)
    lines = [f"🔗 <b>ОЖИДАЮЩИЕ РЕФЕРАЛЬНЫЕ ВЫПЛАТЫ</b>\n\n💰 Всего: {total:.2f} RUB\n"]
    for item in summary[:10]:
        # Показываем тег вместо имени для рефералов
        display_name = item.get('referrer_tag', f"@{item['referrer_username']}" if item.get('referrer_username') else item.get('referrer_name', 'N/A'))
        lines.append(f"🏷 {display_name} • {item['total_unpaid']:.0f} ₽ ({item['count']})")
    
    await edit_with_brand(callback, "\n".join(lines), reply_markup=get_referral_payout_keyboard(summary))


@router.callback_query(F.data == "payouts_mentors")
@admin_only
async def show_mentor_payouts(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    
    summary = await get_unpaid_mentor_summary()
    if not summary:
        await edit_with_brand(callback, "👨‍🏫 <b>ВЫПЛАТЫ НАСТАВНИКАМ</b>\n\nНет ожидающих.", reply_markup=get_back_to_admin_keyboard())
        return
    
    total = sum(item['total_unpaid'] for item in summary)
    lines = [f"👨‍🏫 <b>ОЖИДАЮЩИЕ ВЫПЛАТЫ НАСТАВНИКАМ</b>\n\n💰 Всего: {total:.2f} RUB\n"]
    for item in summary[:10]:
        # Показываем тег вместо имени для наставников
        display_name = item.get('mentor_tag', f"@{item['mentor_username']}" if item.get('mentor_username') else item.get('mentor_name', 'N/A'))
        lines.append(f"🏷 {display_name} • {item['total_unpaid']:.0f} ₽ ({item['count']})")
    
    await edit_with_brand(callback, "\n".join(lines), reply_markup=get_mentor_payout_keyboard(summary))


@router.callback_query(F.data == "payout_all")
@admin_only
async def payout_all(callback: CallbackQuery) -> None:
    await callback.answer("Выплата всем...")
    from utils.messages import edit_with_brand
    
    summary = await get_unpaid_summary()
    if not summary:
        await edit_with_brand(callback, "❌ Нет ожидающих выплат", reply_markup=get_back_to_admin_keyboard())
        return
    
    count = 0
    for item in summary:
        await mark_profits_paid(item['user_id'])
        try:
            await callback.bot.send_message(item['user_id'], "💸 <b>ВЫПЛАТА ОТПРАВЛЕНА!</b>\n\nПроверьте кошелек. 💎")
        except:
            pass
        count += 1
    
    await log_admin_action(callback.from_user.id, callback.from_user.username, "payout_all", f"Выплачено {count} воркерам")
    await edit_with_brand(callback, f"✅ Выплачено {count} воркерам!", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data.startswith("payout_"))
@admin_only
async def process_payout(callback: CallbackQuery) -> None:
    if callback.data == "payout_all":
        return
    await callback.answer("Обработка...")
    
    user_id = int(callback.data.split("_")[1])
    count = await mark_profits_paid(user_id)
    user = await get_user(user_id)
    
    await log_admin_action(callback.from_user.id, callback.from_user.username, "payout", f"@{user['username']} ({count})", user_id)
    
    try:
        await callback.bot.send_message(user_id, "💸 <b>ВЫПЛАТА ОТПРАВЛЕНА!</b>\n\nПроверьте кошелек. 💎")
    except:
        pass
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"✅ Выплата: {user['full_name']}\nПрофитов: {count}", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data.startswith("refpayout_"))
@admin_only
async def process_referral_payout(callback: CallbackQuery) -> None:
    await callback.answer("Обработка...")
    
    user_id = int(callback.data.split("_")[1])
    count = await mark_referral_profits_paid(user_id)
    user = await get_user(user_id)
    
    await log_admin_action(callback.from_user.id, callback.from_user.username, "referral_payout", f"@{user['username']} ({count})", user_id)
    
    try:
        await callback.bot.send_message(user_id, "🔗 <b>РЕФЕРАЛЬНАЯ ВЫПЛАТА!</b>\n\nПроверьте кошелек. 💎")
    except:
        pass
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"✅ Реферальная выплата: {user['full_name']}\nНачислений: {count}", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data.startswith("mentorpayout_"))
@admin_only
async def process_mentor_payout(callback: CallbackQuery) -> None:
    await callback.answer("Обработка...")
    
    user_id = int(callback.data.split("_")[1])
    count = await mark_mentor_profits_paid(user_id)
    user = await get_user(user_id)
    
    await log_admin_action(callback.from_user.id, callback.from_user.username, "mentor_payout", f"@{user['username']} ({count})", user_id)
    
    try:
        await callback.bot.send_message(user_id, "👨‍🏫 <b>ВЫПЛАТА ЗА НАСТАВНИЧЕСТВО!</b>\n\nПроверьте кошелек. 💎")
    except:
        pass
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"✅ Выплата наставнику: {user['full_name']}\nНачислений: {count}", reply_markup=get_back_to_admin_keyboard())


# ============================================
# USERS MANAGEMENT
# ============================================

@router.callback_query(F.data == "manage_users")
@admin_only
async def show_users_management(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\nВыберите действие:", reply_markup=get_users_management_keyboard())


@router.callback_query(F.data == "find_user")
@admin_only
async def find_user_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    from states.all_states import AdminContentState
    await state.set_state(AdminContentState.waiting_for_data)
    await state.update_data(action="find_user")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "🔍 <b>ПОИСК</b>\n\nВведите @username или ID:")


@router.message(AdminContentState.waiting_for_data)
@admin_only
async def find_user_process(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    
    if data.get("action") == "find_user":
        input_text = message.text.strip().lstrip("@")
        user = await get_user(int(input_text)) if input_text.isdigit() else await get_user_by_username(input_text)
        
        if not user:
            await message.answer("❌ Пользователь не найден", reply_markup=get_back_to_admin_keyboard())
            await state.clear()
            return
        
        status_text = {"active": "🟢 Активен", "pending": "⏳ Ожидает", "banned": "🔴 Заблокирован"}.get(user['status'], user['status'])
        text = (
            f"👤 <b>{user['full_name']}</b>\n"
            f"📱 @{user['username']}\n"
            f"🆔 <code>{user['id']}</code>\n"
            f"📊 {status_text}\n"
            f"💰 Кошелек: {user.get('wallet_address', 'Не указан')}"
        )
        
        await message.answer(text, reply_markup=get_user_action_keyboard(user['id'], user['status']))
        await state.clear()
        return
    
    # Handle content data (services/resources)
    lines = message.text.strip().split("\n")
    parsed = {}
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            parsed[k.strip().lower()] = v.strip()
    
    try:
        if data.get("category") == "services":
            name = parsed.get("name")
            if not name:
                raise ValueError("Name required")
            await add_service(name, parsed.get("icon", "🔹"), parsed.get("description"), parsed.get("manual"), parsed.get("bot"))
            await message.answer(f"✅ Сервис добавлен: {name}", reply_markup=get_back_to_admin_keyboard())
        else:
            title, link = parsed.get("title"), parsed.get("link")
            if not title or not link:
                raise ValueError("Title и Link required")
            await add_resource(title, link, data.get("resource_type", "resource"))
            await message.answer(f"✅ Ресурс добавлен: {title}", reply_markup=get_back_to_admin_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        return
    
    await state.clear()


@router.callback_query(F.data == "list_active_users")
@admin_only
async def list_active_users(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    users = await get_users_by_status("active")
    await state.update_data(users_list=users, users_filter="active")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"🟢 <b>АКТИВНЫЕ ({len(users)})</b>", reply_markup=get_user_list_keyboard(users))


@router.callback_query(F.data == "list_pending_users")
@admin_only
async def list_pending_users(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    users = await get_users_by_status("pending")
    await state.update_data(users_list=users, users_filter="pending")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"⏳ <b>ОЖИДАЮЩИЕ ({len(users)})</b>", reply_markup=get_user_list_keyboard(users))


@router.callback_query(F.data == "list_banned_users")
@admin_only
async def list_banned_users(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    users = await get_users_by_status("banned")
    await state.update_data(users_list=users, users_filter="banned")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"🔴 <b>ЗАБЛОКИРОВАННЫЕ ({len(users)})</b>", reply_markup=get_user_list_keyboard(users))


@router.callback_query(F.data.startswith("users_page_"))
@admin_only
async def users_page(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    page = int(callback.data.split("_")[2])
    data = await state.get_data()
    users = data.get("users_list", [])
    
    from utils.messages import edit_with_brand
    filter_name = {"active": "🟢 АКТИВНЫЕ", "pending": "⏳ ОЖИДАЮЩИЕ", "banned": "🔴 ЗАБЛОКИРОВАННЫЕ"}.get(data.get("users_filter", ""), "")
    await edit_with_brand(callback, f"{filter_name} ({len(users)})", reply_markup=get_user_list_keyboard(users, page))


@router.callback_query(F.data.startswith("view_user_"))
@admin_only
async def view_user(callback: CallbackQuery) -> None:
    await callback.answer()
    user_id = int(callback.data.split("_")[2])
    user = await get_user(user_id)
    
    if not user:
        from utils.messages import edit_with_brand
        await edit_with_brand(callback, "❌ Пользователь не найден", reply_markup=get_back_to_admin_keyboard())
        return
    
    status_text = {"active": "🟢 Активен", "pending": "⏳ Ожидает", "banned": "🔴 Заблокирован"}.get(user['status'], user['status'])
    text = (
        f"👤 <b>{user['full_name']}</b>\n"
        f"📱 @{user['username']}\n"
        f"🆔 <code>{user['id']}</code>\n"
        f"📊 {status_text}\n"
        f"💰 Кошелек: {user.get('wallet_address', 'Не указан')}"
    )
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, text, reply_markup=get_user_action_keyboard(user['id'], user['status']))


@router.callback_query(F.data.startswith("ban_user_"))
@admin_only
async def ban_user_handler(callback: CallbackQuery) -> None:
    await callback.answer("Блокировка...")
    user_id = int(callback.data.split("_")[2])
    
    await ban_user(user_id)
    await log_admin_action(callback.from_user.id, callback.from_user.username, "ban_user", f"ID: {user_id}", user_id)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"🚫 Пользователь {user_id} заблокирован", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data.startswith("unban_user_"))
@admin_only
async def unban_user_handler(callback: CallbackQuery) -> None:
    await callback.answer("Разблокировка...")
    user_id = int(callback.data.split("_")[2])
    
    await unban_user(user_id)
    await log_admin_action(callback.from_user.id, callback.from_user.username, "unban_user", f"ID: {user_id}", user_id)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"✅ Пользователь {user_id} разблокирован", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data.startswith("user_profits_"))
@admin_only
async def user_profits(callback: CallbackQuery) -> None:
    await callback.answer()
    user_id = int(callback.data.split("_")[2])
    
    profits = await get_user_profits(user_id, 20)
    user = await get_user(user_id)
    
    if not profits:
        from utils.messages import edit_with_brand
        await edit_with_brand(callback, f"💰 <b>ПРОФИТЫ @{user['username']}</b>\n\nНет профитов", reply_markup=get_back_to_admin_keyboard())
        return
    
    lines = [f"💰 <b>ПРОФИТЫ @{user['username']}</b>\n"]
    total = 0
    for p in profits[:15]:
        status = "✅" if p['status'] == 'paid' else "⏳"
        lines.append(f"{status} {p['service_name']} • {p['net_profit']:.0f} ₽")
        total += p['net_profit']
    
    lines.append(f"\n💵 Всего: {total:.0f} ₽")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "\n".join(lines), reply_markup=get_back_to_admin_keyboard())


# ============================================
# STATISTICS
# ============================================

@router.callback_query(F.data == "admin_stats")
@admin_only
async def show_stats(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "📊 <b>СТАТИСТИКА</b>\n\nВыберите период:", reply_markup=get_stats_keyboard())


@router.callback_query(F.data.startswith("stats_"))
@admin_only
async def show_stats_period(callback: CallbackQuery) -> None:
    await callback.answer()
    period = callback.data.split("_")[1]
    
    if period == "top":
        from database import get_top_workers
        top = await get_top_workers("all", 15)
        
        if not top:
            from utils.messages import edit_with_brand
            await edit_with_brand(callback, "🏆 <b>ТОП ВОРКЕРОВ</b>\n\nПока нет данных", reply_markup=get_back_to_admin_keyboard())
            return
        
        lines = ["🏆 <b>ТОП ВОРКЕРОВ</b>\n"]
        medals = ["🥇", "🥈", "🥉"]
        for i, w in enumerate(top):
            medal = medals[i] if i < 3 else f"{i+1}."
            # Показываем тег вместо имени в топе
            display_name = w.get('user_tag', f"@{w['username']}" if w.get('username') else w.get('full_name', 'N/A'))
            lines.append(f"{medal} {display_name} • {w['total_profit']:.0f} ₽")
        
        from utils.messages import edit_with_brand
        await edit_with_brand(callback, "\n".join(lines), reply_markup=get_back_to_admin_keyboard())
        return
    
    stats = await get_team_stats_by_period(period)
    
    period_names = {"today": "СЕГОДНЯ", "week": "НЕДЕЛЯ", "month": "МЕСЯЦ", "all": "ВСЁ ВРЕМЯ"}
    
    text = (
        f"📊 <b>СТАТИСТИКА: {period_names.get(period, period.upper())}</b>\n\n"
        f"💰 Профит: {stats['total_profit']:.0f} ₽\n"
        f"📈 Профитов: {stats['profits_count']}\n"
        f"👥 Активных: {stats['active_workers']}\n"
        f"💵 Средний: {stats['avg_profit']:.0f} ₽"
    )
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, text, reply_markup=get_back_to_admin_keyboard())


# ============================================
# CONTENT MANAGEMENT
# ============================================

@router.callback_query(F.data == "manage_content")
@admin_only
async def show_content_management(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminContentState.waiting_for_category)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "⚙️ <b>КОНТЕНТ</b>\n\nЧто настраиваем?", reply_markup=get_content_category_keyboard())


@router.callback_query(F.data == "manage_services", AdminContentState.waiting_for_category)
@admin_only
async def manage_services(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(category="services")
    await state.set_state(AdminContentState.waiting_for_action)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "🛠 <b>СЕРВИСЫ</b>", reply_markup=get_content_action_keyboard())


@router.callback_query(F.data == "manage_resources", AdminContentState.waiting_for_category)
@admin_only
async def manage_resources(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(category="resources")
    await state.set_state(AdminContentState.waiting_for_action)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "📚 <b>РЕСУРСЫ</b>", reply_markup=get_content_action_keyboard())


@router.callback_query(F.data == "content_add", AdminContentState.waiting_for_action)
@admin_only
async def start_add_content(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    
    from utils.messages import edit_with_brand
    
    if data["category"] == "services":
        await state.set_state(AdminContentState.waiting_for_data)
        await edit_with_brand(callback,
            "➕ <b>ДОБАВИТЬ СЕРВИС</b>\n\n"
            "<code>Name: Название\nIcon: 🔹\nDescription: Описание\nManual: https://...\nBot: https://t.me/...</code>"
        )
    else:
        await state.set_state(AdminContentState.waiting_for_resource_type)
        await edit_with_brand(callback, "➕ <b>ТИП РЕСУРСА</b>", reply_markup=get_resource_type_keyboard())


@router.callback_query(F.data == "content_list", AdminContentState.waiting_for_action)
@admin_only
async def show_content_list(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    
    from utils.messages import edit_with_brand
    
    if data["category"] == "services":
        services = await get_services()
        if not services:
            await edit_with_brand(callback, "📋 <b>СЕРВИСЫ</b>\n\nПусто", reply_markup=get_back_to_admin_keyboard())
            return
        
        lines = ["📋 <b>СЕРВИСЫ</b>\n"]
        for s in services:
            lines.append(f"{s.get('icon', '🔹')} {s['name']}")
        await edit_with_brand(callback, "\n".join(lines), reply_markup=get_back_to_admin_keyboard())
    else:
        resources = await get_resources()
        if not resources:
            await edit_with_brand(callback, "📋 <b>РЕСУРСЫ</b>\n\nПусто", reply_markup=get_back_to_admin_keyboard())
            return
        
        lines = ["📋 <b>РЕСУРСЫ</b>\n"]
        for r in resources:
            icon = "👥" if r["type"] == "community" else "📚"
            lines.append(f"{icon} {r['title']}")
        await edit_with_brand(callback, "\n".join(lines), reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data.in_(["resource_type_community", "resource_type_resource"]), AdminContentState.waiting_for_resource_type)
@admin_only
async def select_resource_type(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    res_type = "community" if "community" in callback.data else "resource"
    await state.update_data(resource_type=res_type)
    await state.set_state(AdminContentState.waiting_for_data)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"➕ <b>ДОБАВИТЬ</b>\n\n<code>Title: Название\nLink: https://...</code>")


@router.callback_query(F.data == "content_delete", AdminContentState.waiting_for_action)
@admin_only
async def start_delete_content(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    await state.set_state(AdminContentState.waiting_for_data)
    
    from utils.messages import edit_with_brand
    
    if data["category"] == "services":
        services = await get_services()
        if not services:
            await edit_with_brand(callback, "❌ Нет сервисов.", reply_markup=get_back_to_admin_keyboard())
            await state.clear()
            return
        await edit_with_brand(callback, "🗑 <b>УДАЛИТЬ СЕРВИС</b>", reply_markup=get_service_list_keyboard(services))
    else:
        resources = await get_resources()
        if not resources:
            await edit_with_brand(callback, "❌ Нет ресурсов.", reply_markup=get_back_to_admin_keyboard())
            await state.clear()
            return
        await edit_with_brand(callback, "🗑 <b>УДАЛИТЬ РЕСУРС</b>", reply_markup=get_resource_list_keyboard(resources))


@router.callback_query(F.data.startswith("delete_service_"), AdminContentState.waiting_for_data)
@admin_only
async def delete_service_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await delete_service(int(callback.data.split("_")[2]))
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "✅ Сервис удален!", reply_markup=get_back_to_admin_keyboard())
    await state.clear()


@router.callback_query(F.data.startswith("delete_resource_"), AdminContentState.waiting_for_data)
@admin_only
async def delete_resource_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await delete_resource(int(callback.data.split("_")[2]))
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "✅ Ресурс удален!", reply_markup=get_back_to_admin_keyboard())
    await state.clear()
