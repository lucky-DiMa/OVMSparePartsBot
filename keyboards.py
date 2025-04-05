from aiogram import types
from classes import User
from query_utils import query_type_name


def query_keyboard(user: User, type_: str) -> types.InlineKeyboardMarkup:
    next_type = list(query_type_name.keys())[(list(query_type_name.keys()).index(type_) + 1) % len(list(query_type_name.keys()))]
    inline_kb = []
    # if user.previous_query != '':
    # inline_kb.append([types.InlineKeyboardButton(text=f'Ввести "{user.previous_query}"',
    #                                              callback_data=f'SEARCH "{user.previous_query}"')])
    inline_kb.append([types.InlineKeyboardButton(text=f'Тип запроса: {query_type_name[type_]}', callback_data=f'SET_QUERY_TYPE {next_type}')])
    inline_kb.append([types.InlineKeyboardButton(text='<< ПОМОЩЬ >>', callback_data=f'HELP TYPING QUERY {type_}')])
    inline_kb.append([types.InlineKeyboardButton(text='<< ОТМЕНА >>',
                                                 callback_data='CANCEL TYPING QUERY')])
    markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    return markup
