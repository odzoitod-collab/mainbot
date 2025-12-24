"""Admin mentor management handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.all_states import AdminMentorState
from keyboards.admin_kb import get_back_to_admin_keyboard, get_mentor_list_keyboard
from database import get_user, add_mentor, get_mentors, delete_mentor, get_services
from middlewares.admin import admin_only

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "manage_mentors")
@admin_only
async def show_mentor_management(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    
    mentors = await get_mentors()
    text = f"👨‍🏫 <b>НАСТАВНИКИ</b>\n\nВсего: {len(mentors)}"
    
    await edit_with_brand(callback, text, reply_markup=get_mentor_list_keyboard(mentors))


@router.callback_query(F.data == "add_mentor")
@admin_only
async def start_add_mentor(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminMentorState.waiting_for_user_id)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "➕ <b>ДОБАВИТЬ НАСТАВНИКА</b>\n\nID пользователя:")


@router.message(AdminMentorState.waiting_for_user_id)
@admin_only
async def receive_mentor_user_id(message: Message, state: FSMContext) -> None:
    try:
        user_id = int(message.text.strip())
        user = await get_user(user_id)
        
        if not user:
            await message.answer("❌ Не найден:")
            return
        
        if user["status"] != "active":
            await message.answer("❌ Должен быть активным:")
            return
        
        await state.update_data(user_id=user_id, user_name=user["full_name"], username=user["username"])
        await state.set_state(AdminMentorState.waiting_for_service)
        
        services = await get_services()
        service_list = "\n".join([f"• {s['name']}" for s in services])
        
        await message.answer(f"✅ {user['full_name']}\n\nСервисы:\n{service_list}\n\nНазвание сервиса:")
    except ValueError:
        await message.answer("❌ Число:")


@router.message(AdminMentorState.waiting_for_service)
@admin_only
async def receive_mentor_service(message: Message, state: FSMContext) -> None:
    service_name = message.text.strip()
    services = await get_services()
    
    if service_name not in [s['name'] for s in services]:
        await message.answer("❌ Не найден. Точное название:")
        return
    
    await state.update_data(service_name=service_name)
    await state.set_state(AdminMentorState.waiting_for_percent)
    await message.answer(f"✅ {service_name}\n\nПроцент (1-50):")


@router.message(AdminMentorState.waiting_for_percent)
@admin_only
async def receive_mentor_percent(message: Message, state: FSMContext) -> None:
    try:
        percent = int(message.text.strip().replace("%", ""))
        if not 1 <= percent <= 50:
            raise ValueError()
        
        data = await state.get_data()
        await state.clear()
        
        mentor_id = await add_mentor(data["user_id"], data["service_name"], percent)
        
        await message.answer(
            f"✅ <b>НАСТАВНИК #{mentor_id}</b>\n\n"
            f"👤 {data['user_name']} (@{data['username']})\n"
            f"🛠 {data['service_name']}\n"
            f"💰 {percent}%",
            reply_markup=get_back_to_admin_keyboard()
        )
    except ValueError:
        await message.answer("❌ 1-50:")


@router.callback_query(F.data.startswith("delete_mentor_"))
@admin_only
async def delete_mentor_confirm(callback: CallbackQuery) -> None:
    await callback.answer()
    await delete_mentor(int(callback.data.split("_")[2]))
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "✅ Наставник удален!", reply_markup=get_back_to_admin_keyboard())
