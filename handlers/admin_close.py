"""Admin utility handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from middlewares.admin import admin_only

router = Router()


@router.callback_query(F.data == "close_admin")
@admin_only
async def close_admin_panel(callback: CallbackQuery) -> None:
    await callback.answer("Закрыто")
    await callback.message.delete()
