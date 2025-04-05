from aiogram import types


query_type_name = {"single": 'обычный',
                   "multi": "мульти"}

def get_query_type(message: types.Message):
    if len(message.reply_markup.inline_keyboard) < 2:
        return None
    return message.reply_markup.inline_keyboard[0][0].callback_data.split()[-1]

def get_query_text(message: types.Message):
    return message.text.split('\n')[0][8:]