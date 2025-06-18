from aiogram import Router

from .text_scripts import text_messages_router
from .callback_scripts import callback_queries_router

router = Router()
router.include_routers(text_messages_router, callback_queries_router)

__all__ = ['router']