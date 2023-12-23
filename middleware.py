from aiogram.dispatcher.flags import get_flag

from config import is_command
from classes import User
from create_bot import dp
from aiogram import types


async def get_user_update_outer_middleware(handler: callable,
                                           event: types.Update,
                                           data: dict):
    data['user_exists'] = User.exists_by_id(event.event.from_user.id)
    data['user'] = User.get_by_id(event.event.from_user.id) if data['user_exists'] else None
    await handler(event, data)


# async def state_message_checker_callback_query_middleware(handler: callable, event: types.Update, data: dict):
#     check_state_message = get_flag(data, 'check_state_message', default=False)
#     if check_state_message and event.message.message_id != data["user"].id_of_message_promoter_to_type:
#         return await event.answer('Сообщение устарело!', True)
#     return await handler(event, data)
#
#
# async def state_checker_callback_query_middleware(handler: callable, event: types.Update, data: dict):
#     state_filter: StateFilter = get_flag(data, 'state_filter', default=None)
#     if state_filter is not None and not state_filter(user=data["user"]):
#         return await event.answer(get_flag(data, 'state_error_message'), True)
#     return await handler(event, data)


def register_middleware():
    dp.update.outer_middleware.register(get_user_update_outer_middleware)
    # dp.callback_query.middleware.register(state_checker_callback_query_middleware)
    # dp.callback_query.middleware.register(state_message_checker_callback_query_middleware)
