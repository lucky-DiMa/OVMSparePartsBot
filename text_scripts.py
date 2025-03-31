from asyncio import sleep
from datetime import datetime
from aiogram.enums import ContentType
from aiogram.filters import Command
from classes import User, Query, SparePart
from aiogram import types, F
from config import is_command, text_of_contacts_message
from create_bot import dp, bot
from filters import StateFilter
from keyboards import query_keyboard


async def cannot_use_command(message: types.Message):
    await message.delete()
    text = 'Сначала введите поисковой запрос в поле "сообщение"!' if User.get_by_id(
        message.from_user.id).state.startswith(
        'TYPING QUERY') else 'Напишите сообщение обратной связи сообщение обратной свази!'
    temp_msg = await message.answer(f'{text}')
    await sleep(5)
    await temp_msg.delete()
    return


async def start(message: types.Message, user_exists: bool, user: User):
    if not user_exists:
        user = User.reg(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text='Поделиться', request_contact=True)]],
                                       resize_keyboard=True)
    await message.answer(
        f'Здравствуйте {message.from_user.full_name}!\nЯ бот компании ОМПартс, которая входит в группу компаний ТД Овоще-молочного, помогу вам с лёгкостью найти любую запчасть, если она есть в нашей БД!\n\n{"" if user.phone != "" else "Пожалуйста поделись со мной своим контактом Telegram с помощью кнопки ниже чтобы занёс ваш номер в свою базу данных, если вы не хотите чтобы я хранил ваш номер то, к сожалению, вы не сможете использовать этого бота!"}',
        reply_markup=None if user.phone != "" else markup)

    user.state = user.state if User.get_by_id(
        message.from_user.id).phone != "" else "SENDING CONTACT"
    await message.delete()


# async def get_ph(message: types.Message):
#     reg(message.from_user.id)
#     if user.state == 'TYPING QUERY':
#         await message.delete()
#         temp_msg = await message.answer('Вы сейчас вводите запрос!')
#         await sleep(1.5)
#         await temp_msg.delete()
#         return
#     for sp in db:
#         if sp.photo_link != '':
#             await message.answer_photo(sp.photo_link, f'Бренд: {sp.brand}\nНаименование: {sp.name}\nАртикул: {sp.code}\nОригинальный артикул: {sp.code}\nПрименяемость: {sp.usage}')
#     await message.delete()


async def contacts(message: types.Message):
    await message.delete()
    await message.answer(text_of_contacts_message)


async def query_message(message: types.Message, user: User):
    if len(message.text) < 4:
        await message.reply('Минимальная длина запроса - 4 символа!')
        return
    user.state = 'NONE'
    await message.delete()
    await bot.edit_message_text('Запрос обрабатывается, это займёт меньше минуты...', chat_id=message.from_user.id, message_id=user.id_of_message_promoter_to_type)
    query = Query.create(message.from_user.id, message.text, user.id_of_message_promoter_to_type)
    user.previous_query = message.text
    result = await query.get_result()
    text = f'Найдено {len(result.spare_parts)} запчаст{"ь" if len(result.spare_parts) == 1 else "и"} {len(result.brands)} бренд{"а" if len(result.brands) == 1 else "ов"} по запросу "{message.text}":' if len(result.spare_parts) > 0 else f'Не найдено запчастей по запросу "{message.text}"!'
    await bot.edit_message_text(text, chat_id=user.id, message_id=user.id_of_message_promoter_to_type,
                                reply_markup=result.brands_pages_keyboard(1))


async def feedback(message: types.Message, user: User):
    await message.delete()
    user.state = 'TYPING FEEDBACK'
    bot_message = await message.answer(
        'Напишите мне что вам понравилось или не понравилось во мне, а также то, чтобы вы хотели ещё от меня!\nНапишите всё в **одном сообщении**, можно даже прислать фото, например запчасти, которую вы у меня не нашли!',
        'MARKDOWN', reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='<< ОТМЕНА >>', callback_data='CANCEL TYPING FEEDBACK')]]))
    user.id_of_message_promoter_to_type = bot_message.message_id
    user.text_of_message_promoter_to_type = bot_message.text


async def feedback_msg(message: types.Message, user: User):
    user.state = 'NONE'
    await bot.edit_message_reply_markup(chat_id=user.id, message_id=user.id_of_message_promoter_to_type)
    await message.answer('Спасибо за то, что даёте обратную связь, возможно мы прислушаемся к вам!')
    await message.forward(-1001778865158)


async def contact(message: types.Message, user: User):
    if message.contact is None:
        markup = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text='Поделиться', request_contact=True)]], resize_keyboard=True)
        await message.answer(user.end_type_text, reply_markup=markup)
        return
    if message.contact.user_id != message.from_user.id:
        markup = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text='Поделиться', request_contact=True)]], resize_keyboard=True)
        await message.answer('Вы отправили чужой контакт!', reply_markup=markup)
        return
    user.state = 'NONE'
    user.phone = message.contact.phone_number
    if not user.phone.startswith('+'):
        user.phone = '+' + user.phone
    await message.answer(f'Номер {user.phone} сохранён регистрация завершена!',
                         reply_markup=types.ReplyKeyboardRemove())


async def all_messages(message: types.Message):
    await message.reply('Что вы говорите??')


async def search(message: types.Message, user: User):
    if user.state != 'NONE':
        await message.reply(user.end_type_text)
        return
    markup = query_keyboard(user, 'single')
    user.id_of_message_promoter_to_type = (
        await message.answer("Отправьте поисковой запрос!", reply_markup=markup)).message_id
    user.state = 'TYPING QUERY'
    await message.delete()


async def no(message: types.Message):
    pass


async def problem_with_username(message: types.Message):
    if is_command(message) is not None:
        await message.delete()
    await message.answer(
        'Извините, но я не могу с вами работать, так как у вас нету имени пользователя в Telegram!\nПожалуйста добавьте имя полльзователя в настройках профиля и приходите обратно!\nСпасибо за понимание!')
    #
    # await message.answer('Извините, но я не могу с вами работать, так как у вас нету имени пользователя в Telegram!\nПожалуйста добавьте имя полльзователя в настройках профиля и приходите обратно!\nСпасибо за понимание!')


# async def set_phone(message: types.Message):
#     await client.connect()
#     acc = await client.get_entity(message.from_user.id)
#     await client.disconnect()
#     await message.delete()
#     if acc.phone is None:
#         await message.answer('Извините, но я не знаю вашего номера телефона!\nЧтобы я его увидел пожалуйста зайдите в настройки приватности и включите видимость номера телефона для всех, для всех!\nЗатем зайдите в бота и используйте команду /setphone, я должен написать что номер сохранён!\nПосле моего подтверждение, что номер сохрвнён вы можете выключать видимость номера обратно, если хотите конечно!')
#     else:
#         user.phone = acc.phone
#         await message.answer(f'Номер +{acc.phone} сохранён!')
#         if user.state == 'NONE' and is_command(message) is not None:
#             match is_command(message).lower():
#                 case 'start':
#                     await start(message)
#                 case 'feedback':
#                     await feedback(message)
#                 case 'search':
#                     await search(message)
#                 case 'contacts':
#                     await contacts(message)
#                 case _:
#                     await all_messages(message)
#         elif user.state == 'NONE' and is_command(message) is None:
#             await all_messages(message)
#         elif user.state != 'NONE' and is_command(message) is not None:
#             await cannot_use_command(message)
#         elif user.state == 'TYPING QUERY' and is_command(message) is None:
#             await query(message)
#         elif user.state == 'TYPING FEEDBACK' and is_command(message) is None:
#             await feedback_msg(message)
#         else:
#             await all_messages(message)


# async def problem_with_phone(message: types.Message):
#     if is_command(message) is not None:
#         await message.delete()
#     await message.answer('Извините, но я не могу с вами работать т. к. не знаю вашего номера телефона!\nЧтобы я его сохранил используйте команду /setphone\nСпасибо за понимание!')


async def restart_command(message: types.Message):
    await message.delete()
    await message.answer('RESTARTING...')
    import os
    os.system("bash main.sh")


async def delete_me(message: types.Message):
    User.del_by_id(message.from_user.id)
    await message.delete()


async def delete_all(message: types.Message):
    await message.delete()
    User.delete_all()
    Query.delete_all()
    await message.answer('ALL DELETED')


async def get_a_q_command(_):
    json_list = []
    for q in Query.get_all():
        json_list.append(q.to_JSON())
    print(json_list)


def reg_handlers():
    dp.message.register(no, lambda message: message.chat.type in ['group', 'supergroup'])
    dp.message.register(problem_with_username, lambda message: message.from_user.username is None)
    dp.message.register(start, lambda _, user_exists: not user_exists,
                        F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.CONTACT]))
    dp.message.register(contact, StateFilter('SENDING CONTACT'),
                        F.content_type.in_([ContentType.TEXT, ContentType.CONTACT]))
    dp.message.register(query_message, StateFilter('TYPING QUERY'),
                        F.content_type.in_([ContentType.TEXT, ContentType.PHOTO]))
    dp.message.register(feedback_msg, StateFilter('TYPING FEEDBACK'),
                        F.content_type.in_([ContentType.TEXT, ContentType.PHOTO]))
    dp.message.register(start, Command('start'), F.content_type == ContentType.TEXT)
    dp.message.register(feedback, Command('feedback'), F.content_type == ContentType.TEXT)
    dp.message.register(search, Command('search'), F.content_type == ContentType.TEXT)
    dp.message.register(delete_me, lambda message: message.from_user.id == 1358414277, Command('delete_me'),
                        F.content_type == ContentType.TEXT)
    dp.message.register(get_a_q_command, lambda message: message.from_user.id == 1358414277, Command('get_a_q'),
                        F.content_type == ContentType.TEXT)
    dp.message.register(delete_all, lambda message: message.from_user.id == 1358414277, Command('delete_all'),
                        F.content_type == ContentType.TEXT)
    dp.message.register(restart_command, lambda message: message.from_user.id in [1358414277],
                        Command('restart'), F.content_type == ContentType.TEXT)
    dp.message.register(contacts, Command('contacts'), F.content_type == ContentType.TEXT)
    dp.message.register(all_messages)
