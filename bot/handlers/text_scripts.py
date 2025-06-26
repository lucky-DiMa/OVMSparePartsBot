from asyncio import sleep
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandObject
from classes import User, SingleQuery, AnalogSearchResult, AccessRequest
from aiogram import types, F, Router
from bot.filters import is_command, StateFilter
from classes import MultiQuery
from config import text_of_contacts_message, ACCESS_KEY
from bot.create_bot import bot
from bot.keyboards import query_keyboard
from utils import morph


async def cannot_use_command(message: types.Message):
    await message.delete()
    text = 'Сначала введите поисковой запрос в поле "сообщение"!' if User.get_by_id(
        message.from_user.id).state.startswith(
        'TYPING QUERY') else 'Напишите сообщение обратной связи!'
    temp_msg = await message.answer(f'{text}')
    await sleep(5)
    await temp_msg.delete()
    return


async def start(message: types.Message, user_exists: bool, user: User, command: CommandObject = None):
    await message.delete()
    if not user_exists:
        user = User.reg(message.from_user.id)
    if user.phone != "" and command and command.args.startswith('search-analogs--'):
        res = await AnalogSearchResult.get_by_code(command.args.replace('search-analogs--', '').replace('---space---', ' ').replace('---dot---', '.'))
        await message.answer(res.text, parse_mode='HTML', reply_markup=res.keyboard())
        return
    markup = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text='Поделиться', request_contact=True)]],
                                       resize_keyboard=True)
    await message.answer(
        f'Здравствуйте {message.from_user.full_name}!\nЯ бот компании ООО "ОМ партс", которая входит в группу компаний ТД "Овоще-молочный", помогу вам с лёгкостью найти любую запчасть, если она есть в нашей базе данных!\n\n{"" if user.phone != "" else "Пожалуйста, поделись со мной своим контактом Telegram с помощью кнопки ниже, чтобы я занёс ваш номер в свою базу данных, если вы не хотите чтобы я хранил ваш номер, то, к сожалению, вы не сможете использовать этого бота!"}',
        reply_markup=None if user.phone != "" else markup)

    user.state = user.state if User.get_by_id(
        message.from_user.id).phone != "" else "SENDING CONTACT"


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
    query_type = user.state.split()[-1]
    if query_type == 'single' and len(message.text) < 4:
        msg = await message.reply('Минимальная длина запроса - 4 символа!')
        await sleep(10)
        await message.delete()
        await msg.delete()
        return
    user.state = 'NONE'
    await message.delete()
    await bot.edit_message_text('Запрос обрабатывается, это займёт меньше минуты...', chat_id=message.from_user.id, message_id=user.id_of_message_promoter_to_type)
    match query_type:
        case 'single':
            query = SingleQuery.create(message.from_user.id, message.text)
            user.previous_query = message.text
            result = await query.get_result()
            text = f'Запрос: <code>{message.text}</code>\n\n' + result.get_result_stats_text()
            await bot.edit_message_text(text, parse_mode='HTML', chat_id=user.id, message_id=user.id_of_message_promoter_to_type,
                                        reply_markup=result.brands_pages_keyboard(0))
        case 'multi':
            general_text = 'Статистика мультизапроса:'
            texts = message.text.split('\n')
            right_texts = []
            for text in texts:
                if len(text) < 4:
                    continue
                right_texts.append(text)
            query = MultiQuery.create(user.id, right_texts)
            results = await query.get_results_in_dict()
            await bot.delete_message(user.id, user.id_of_message_promoter_to_type)
            for query_text, query_result in results.items():
                message_text = f'Запрос: <code>{query_text}</code>\n\n' + query_result.get_result_stats_text()
                markup = query_result.brands_pages_keyboard(0)
                await message.answer(message_text, parse_mode='HTML', reply_markup=markup)
            for i, text in enumerate(texts, 1):
                general_text += f'\n{i}. <code>{text}</code> - '
                if len(text) < 4:
                    general_text += '❌ запрос не обработан, минимальная длина запроса - <code>4</code>.'
                else:
                    general_text += '✅ запрос обработан корректно.'
            await message.answer(general_text, parse_mode='HTML', reply_markup=query.general_message_keyboard)


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
    await message.answer('Спасибо за то, что даёте обратную связь, возможно, мы прислушаемся к вам!')
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
    user.phone = message.contact.phone_number
    user.state = 'WAITING FOR REG CONFIRMATION'
    if not user.phone.startswith('+'):
        user.phone = '+' + user.phone
    request = AccessRequest.create(user)
    msg = await message.answer(await request.get_info(True),
                                     reply_markup=AccessRequest.editing_keyboard(), parse_mode='HTML')
    user.id_of_message_promoter_to_type = msg.message_id
    await message.delete()
    for admin in User.get_responders():
        await admin.send_message(
            f"Поступил новый запрос доступа к боту от <code>{request.user_phone}</code>.\nВсего <code>{len(AccessRequest.get_waiting())}</code> запросов, ожидающих подтверждения.",
            markup=types.InlineKeyboardMarkup(
                inline_keyboard=[[types.InlineKeyboardButton(text=f'Посмотреть запрос от {request.user_phone}',
                                                             callback_data=f'VIEW REQUEST {request.id}')],
                                 [types.InlineKeyboardButton(text="Посмотреть все запросы",
                                                             callback_data="UPDATE REQUESTS")]]))


async def all_messages(message: types.Message):
    await message.reply('Что вы говорите??')


async def search(message: types.Message, user: User):
    if user.state != 'NONE':
        await message.reply(user.end_type_text)
        return
    markup = query_keyboard(user, 'single')
    user.id_of_message_promoter_to_type = (
        await message.answer("Отправьте поисковой запрос!", reply_markup=markup)).message_id
    user.state = 'TYPING QUERY single'
    await message.delete()


async def no(_):
    pass


async def problem_with_username(message: types.Message):
    if is_command(message) is not None:
        await message.delete()
    await message.answer(
        'Извините, но я не могу с вами работать, так как у вас нет имени пользователя в Telegram!\nПожалуйста добавьте имя пользователя в настройках профиля и приходите обратно!\nСпасибо за понимание!')
    #
    # await message.answer('Извините, но я не могу с вами работать, так как у вас нет имени пользователя в Telegram!\nПожалуйста добавьте имя пользователя в настройках профиля и приходите обратно!\nСпасибо за понимание!')


# async def set_phone(message: types.Message):
#     await client.connect()
#     acc = await client.get_entity(message.from_user.id)
#     await client.disconnect()
#     await message.delete()
#     if acc.phone is None:
#         await message.answer('Извините, но я не знаю вашего номера телефона!\nЧтобы я его увидел пожалуйста зайдите в настройки приватности и включите видимость номера телефона для всех, для всех!\nЗатем зайдите в бота и используйте команду /setphone, я должен написать что номер сохранён!\nПосле моего подтверждение, что номер сохранён вы можете выключать видимость номера обратно, если хотите конечно!')
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
    os.system("docker compose restart")


async def delete_me(message: types.Message):
    User.delete_by_id(message.from_user.id)
    await message.delete()


async def delete_all(message: types.Message):
    await message.delete()
    User.delete_all()
    SingleQuery.delete_all()
    await message.answer('ALL DELETED')


async def get_a_q_command(_):
    json_list = []
    for q in SingleQuery.get_all():
        json_list.append(q.to_json())
    print(json_list)
    

async def help_command(message: types.Message, user: User):
    await message.delete()
    await message.answer(user.help_message_text, parse_mode='HTML')


async def get_analogs_command(message: types.Message, command: CommandObject):
    res = await AnalogSearchResult.get_by_code(command.args)
    await message.delete()
    await message.answer(res.text, parse_mode='HTML', reply_markup=res.keyboard())


async def cancel_command(message: types.Message, user: User):
    if user.state == 'NONE':
        await user.send_message('Я не просил вас ничего писать :)')
    elif user.state in ["SENDING CONTACT"]:
        user.delete()
        await message.answer('Регистрация отменена!', reply_markup=types.ReplyKeyboardRemove())
    else:
        user.state = 'NONE'
        await user.send_message('Действие отменено!')
    await message.delete()

async def no_access(message: types.Message):
    await message.delete()
    await message.answer('У вас нет доступа к боту!')


async def invite_command(message:types.Message):
    await message.delete()
    await message.answer(f'Чтобы пригласить нового пользователя скопируйте ссылку и отправьте ему.\n\n Ссылка: <code>https://t.me/{(await bot.get_me()).username}?start={ACCESS_KEY}</code>', parse_mode='HTML')


async def requests_command(message:types.Message):
    await message.delete()
    requests = AccessRequest.get_waiting()

    await message.answer(f'<b>{len(requests)}</b> {morph.parse("запрос")[0].make_agree_with_number(len(requests)).word}, ожидающих ответа',
                         reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=request.user_phone, callback_data=f'VIEW REQUEST {request.id}')] for request in requests] + [[types.InlineKeyboardButton(text="↻ Обновить", callback_data="UPDATE REQUESTS")]]),
                         parse_mode='HTML')


async def waiting_for_reg_confirmation(message: types.Message):
    await message.reply('Пожалуйста дождитесь подтверждения регистрации!')


text_messages_router = Router(name='text_messages')
text_messages_router.message.register(no, lambda message: message.chat.type in ['group', 'supergroup'])
text_messages_router.message.register(start, F.text == '/start ' +  ACCESS_KEY, F.content_type == ContentType.TEXT)
text_messages_router.message.register(no_access, lambda _, user_exists: not user_exists)
text_messages_router.message.register(problem_with_username, lambda message: message.from_user.username is None)
text_messages_router.message.register(cancel_command, Command('cancel'), F.content_type == ContentType.TEXT)
text_messages_router.message.register(waiting_for_reg_confirmation,
                        StateFilter('WAITING FOR REG CONFIRMATION'))
text_messages_router.message.register(contact, StateFilter('SENDING CONTACT'),
                    F.content_type.in_([ContentType.TEXT, ContentType.CONTACT]))
text_messages_router.message.register(query_message, StateFilter('TYPING QUERY', True),
                    F.content_type.in_([ContentType.TEXT, ContentType.PHOTO]))
text_messages_router.message.register(feedback_msg, StateFilter('TYPING FEEDBACK'),
                    F.content_type.in_([ContentType.TEXT, ContentType.PHOTO]))
text_messages_router.message.register(start, Command('start'), F.content_type == ContentType.TEXT)
text_messages_router.message.register(help_command, Command('help'), F.content_type == ContentType.TEXT)
text_messages_router.message.register(feedback, Command('feedback'), F.content_type == ContentType.TEXT)
text_messages_router.message.register(search, Command('search'), F.content_type == ContentType.TEXT)
text_messages_router.message.register(delete_me, lambda message: message.from_user.id == 1358414277, Command('delete_me'),
                    F.content_type == ContentType.TEXT)
text_messages_router.message.register(get_a_q_command, lambda message: message.from_user.id == 1358414277, Command('get_a_q'),
                    F.content_type == ContentType.TEXT)
text_messages_router.message.register(delete_all, lambda message: message.from_user.id == 1358414277, Command('delete_all'),
                    F.content_type == ContentType.TEXT)
text_messages_router.message.register(restart_command, lambda message: message.from_user.id in [1358414277],
                    Command('restart'), F.content_type == ContentType.TEXT)
text_messages_router.message.register(invite_command,
                        Command('invite'), F.content_type == ContentType.TEXT,
                        flags={"required_permissions": ["invite_new_users"]})
text_messages_router.message.register(requests_command,
                            Command('requests'), F.content_type == ContentType.TEXT,
                            flags={"required_permissions": ["responder"]})
text_messages_router.message.register(contacts, Command('contacts'), F.content_type == ContentType.TEXT)
text_messages_router.message.register(get_analogs_command, Command('get_analogs'), F.content_type == ContentType.TEXT)
text_messages_router.message.register(all_messages)
