"""Admin direct payments management."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.all_states import AdminDirectPaymentState
from database import get_direct_payment_settings, update_direct_payment_settings
from keyboards.admin_kb import get_back_to_admin_keyboard, get_direct_payments_admin_keyboard
from middlewares.admin import admin_only
from utils.design import header

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "manage_direct_payments")
@admin_only
async def show_direct_payment_settings(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.messages import edit_with_brand
    
    settings = await get_direct_payment_settings()
    
    text = f"{header('ПРЯМИКИ', '💳')}\n\n"
    
    if settings:
        text += f"<b>Реквизиты:</b>\n<code>{settings['requisites']}</code>\n\n"
        if settings.get('additional_info'):
            text += f"<b>Инфо:</b> {settings['additional_info']}\n\n"
        text += f"<b>Поддержка:</b> @{settings['support_username']}\n"
    else:
        text += "<i>Не настроено</i>"
    
    await edit_with_brand(callback, text, reply_markup=get_direct_payments_admin_keyboard())


@router.callback_query(F.data == "edit_requisites")
@admin_only
async def edit_requisites(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminDirectPaymentState.waiting_for_requisites)
    await state.update_data(edit_field="requisites")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "💳 <b>РЕКВИЗИТЫ</b>\n\nВведите новые реквизиты:")


@router.callback_query(F.data == "edit_dp_info")
@admin_only
async def edit_dp_info(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminDirectPaymentState.waiting_for_additional_info)
    await state.update_data(edit_field="info")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "📝 <b>ДОП. ИНФО</b>\n\nВведите дополнительную информацию:")


@router.callback_query(F.data == "edit_support")
@admin_only
async def edit_support(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminDirectPaymentState.waiting_for_support_username)
    await state.update_data(edit_field="support")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "👤 <b>ПОДДЕРЖКА</b>\n\nВведите @username поддержки:")


@router.message(AdminDirectPaymentState.waiting_for_requisites)
@admin_only
async def receive_requisites(message: Message, state: FSMContext) -> None:
    settings = await get_direct_payment_settings() or {}
    
    try:
        await update_direct_payment_settings(
            message.text.strip(),
            settings.get('additional_info', ''),
            settings.get('support_username', 'support')
        )
        await message.answer("✅ Реквизиты обновлены!", reply_markup=get_back_to_admin_keyboard())
        await state.clear()
    except Exception as e:
        logger.error(f"Update failed: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@router.message(AdminDirectPaymentState.waiting_for_additional_info)
@admin_only
async def receive_additional_info(message: Message, state: FSMContext) -> None:
    settings = await get_direct_payment_settings() or {}
    
    try:
        await update_direct_payment_settings(
            settings.get('requisites', 'Не настроено'),
            message.text.strip(),
            settings.get('support_username', 'support')
        )
        await message.answer("✅ Информация обновлена!", reply_markup=get_back_to_admin_keyboard())
        await state.clear()
    except Exception as e:
        logger.error(f"Update failed: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@router.message(AdminDirectPaymentState.waiting_for_support_username)
@admin_only
async def receive_support_username(message: Message, state: FSMContext) -> None:
    settings = await get_direct_payment_settings() or {}
    support = message.text.strip().lstrip("@")
    
    try:
        await update_direct_payment_settings(
            settings.get('requisites', 'Не настроено'),
            settings.get('additional_info', ''),
            support
        )
        await message.answer(f"✅ Поддержка: @{support}", reply_markup=get_back_to_admin_keyboard())
        await state.clear()
    except Exception as e:
        logger.error(f"Update failed: {e}")
        await message.answer(f"❌ Ошибка: {e}")
