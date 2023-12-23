from datetime import datetime
from aiogram.enums import ChatAction
from aiogram import types, F
from classes import Query, SparePart, User, Photo, Brand
from config import text_of_contacts_message
from create_bot import dp, bot


async def callback_for_search_something_btn(query: types.CallbackQuery):
    if User.get_by_id(query.from_user.id).state != 'TYPING QUERY':
        await query.answer('Вы сейчас не отправляете запрос!', show_alert=True)
        await query.message.delete()
        return
    if User.get_by_id(query.from_user.id).id_of_message_promoter_to_type != query.message.message_id:
        await query.answer('Сообщение устарело!', True)
        await query.message.delete()
        return
    user = User.get_by_id(query.from_user.id)
    result = SparePart.search(query.data.split('"')[-2])
    user.state = 'NONE'
    search_query = query.data.split('"')[-2]
    Query.reg(Query(query.message.from_user.id, search_query, datetime.now().hour - 5,
                    datetime.now().minute))
    text = f'Найдено {result.spare_parts_count} запчаст{"ь" if result.spare_parts_count == 1 else "и"} {len(result.brands)} бренд{"а" if len(result.brands) == 1 else "ов"} по запросу "{search_query}":' if result.spare_parts_count > 0 else f'Не найдено запчастей по запросу "{search_query}"!'
    await bot.edit_message_text(text, user.id, user.id_of_message_promoter_to_type,
                                reply_markup=result.brands_pages_keyboard(1))


async def callback_for_goto_sp_page_buttons(query: types.CallbackQuery):
    brand = Brand.get_by_uid(query.data.split('"')[-2])
    if brand is None:
        await query.answer('Этого бренда уже нету в базе!', True)
        return
    result = SparePart.search(query.message.text.split('"')[-2], brand.uid)
    new_page_n = int(query.data.split()[-2])
    if new_page_n == 0:
        await query.answer('Вы находитесь на первой странице!', True)
        return
    if new_page_n - result.sp_pages_count == 1:
        await query.answer('Вы находитесь на последней странице странице!', True)
        return
    if new_page_n > result.sp_pages_count:
        new_page_n = result.sp_pages_count
    await query.message.edit_reply_markup(reply_markup=result.sp_pages_keyboard(new_page_n))


# async def callback_for_back_to_results_btn(query: types.CallbackQuery):
#     search_query = query.message.caption.split('"')[1]
#     brand = 'KUHN' if 'KUHN' in query.message.caption.split('\n')[1] else 'DIECI' if 'DIECI' in query.message.caption.split('\n')[1] else 'CNHi'
#     results = SparePart.search(search_query, brand)
#     text = f'Найденн{"ая" if len(results) == 1 else "ые"} запчаст{"ь" if len(results) == 1 else "и"} бренда {brand.name} по запросу "{search_query}":' if len(
#         results) > 0 else f'Не найдено запчастей бренда {brand.name} по запросу "{search_query}"!'
#     markup = types.InlineKeyboardMarkup(1)
#     for result in results:
#         markup.add(
#             types.InlineKeyboardButton(text=result.naming, callback_data=f'SHOW "{result.article}"'))
#     markup.add(types.InlineKeyboardButton(text='Поискать у других компаний', callback_data='SEARCH AND DELETE CALL.MESSAGE'))
#     markup.add(types.InlineKeyboardButton(text=f'Ввести другой запрос по бренду {brand.name}',
#                                           callback_data=f'CHOOSE BRAND "{brand.uid}"'))

# await query.message.answer(text, reply_markup=markup)
# await query.message.delete()


async def callback_for_show_spare_part_btns(query: types.CallbackQuery):
    article = query.data.split()[-2]
    brand = Brand.get_by_uid(query.data.split('"')[-2])
    await query.answer()
    await bot.send_chat_action(query.from_user.id, ChatAction.TYPING)
    sp = SparePart.get_by_article(article, brand.uid)
    search_query = query.message.text.split('"')[1]
    photos = list(map(Photo, sp.photos))
    text = f'Запрос: "<code>{search_query}</code>".\nБренд: "<code>{sp.brand.name}</code>"\nНаименование: "<code>{sp.naming}</code>"\nАртикул: "<code>{sp.article}</code>"\n\n'
    if sp.counts:
        text += 'В наличии:\n'
    else:
        text += 'Нет в наличии. '
    for count in sp.counts:
        text += f"{count}\n"
    try:
        if len(photos) == 1:
            await query.message.answer_photo(types.InputFile(photos[0].download()), text, parse_mode='HTML')
        elif len(photos) == 0:
            await query.message.answer(text, parse_mode='HTML')
        else:
            media_list = []
            for i, photo in enumerate(photos):
                if i == 0:
                    media_list.append(types.InputMediaPhoto(types.InputFile(photo.download()), caption=text, parse_mode='HTML'))
                    continue
                media_list.append(types.InputMediaPhoto(types.InputFile(photo.download())))
            mg = types.MediaGroup(media_list)
            await query.message.answer_media_group(mg)
    except:
        await query.message.answer(text + '\n\nОшибка, недопустимый размер изображения! Изображение не подгружено!', parse_mode='HTML')
    for photo in photos:
        photo.remove()


async def callback_for_cancel_typing_query_btn(query: types.CallbackQuery):
    if User.get_by_id(query.from_user.id).state != 'TYPING QUERY':
        await query.answer('Вы сейчас не отправляете запрос!', show_alert=True)
        await query.message.delete()
        return
    if User.get_by_id(query.from_user.id).id_of_message_promoter_to_type != query.message.message_id:
        await query.answer('Вы нажали на кнопку из другого сообщения!', show_alert=True)
        await query.message.delete()
        return
    user = User.get_by_id(query.from_user.id)
    user.state = 'NONE'
    await query.message.edit_text('Поиск отменён!', reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text='Искать запчасти!', callback_data='SEARCH AND DELETE CALL.MESSAGE')]]))
    await query.answer('Поиск отменён!')


async def callback_for_help_typing_query_btn(query: types.CallbackQuery):
    if User.get_by_id(query.from_user.id).state != 'TYPING QUERY':
        await query.answer('Вы сейчас не отправляете запрос!', show_alert=True)
        await query.message.delete()
        return
    if User.get_by_id(query.from_user.id).id_of_message_promoter_to_type != query.message.message_id:
        await query.answer('Вы нажали на кнопку из другого сообщения!', show_alert=True)
        await query.message.delete()
        return
    await query.answer('Введите артикул или часть наименования запчасти, которую вы ищите!', show_alert=True)


async def callback_for_contacts_btn(query: types.CallbackQuery):
    await query.message.answer(text_of_contacts_message)


async def callback_for_choose_brand_buttons(query: types.CallbackQuery):
    search_query = query.message.text.split('"')[-2]
    brand_uid = query.data.split('"')[-2]
    result = SparePart.search(search_query, brand_uid)
    await query.message.edit_text(f'{len(result.spare_parts)} запчастей бренда {result.brand.name} по запросу "{search_query}":', reply_markup=result.sp_pages_keyboard(1))


async def callback_for_start_btn(query: types.CallbackQuery):
    if query.data.startswith('SEARCH AND DELETE CALL.MESSAGE'):
        await query.message.delete()
    user = User.get_by_id(query.from_user.id)
    if user.state != 'NONE':
        await query.answer(user.end_type_text, True)
        return
    inline_kb = []
    if user.previous_query != '':
        inline_kb.append([types.InlineKeyboardButton(text=f'Ввести "{user.previous_query}"',
                                              callback_data=f'SEARCH "{user.previous_query}"')])
    inline_kb.append([types.InlineKeyboardButton(text='<< ПОМОЩЬ >>', callback_data='HELP TYPING QUERY')])
    inline_kb.append([types.InlineKeyboardButton(text='<< ОТМЕНА >>',
                                          callback_data='CANCEL TYPING QUERY')])
    markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)

    user.id_of_message_promoter_to_type = (
        await query.message.answer("Отправьте поисковой запрос!", reply_markup=markup)).message_id
    user.state = 'TYPING QUERY'


async def callback_for_need_new_brand_btn(query: types.CallbackQuery):
    await query.answer('Напишите об этом в обратой связи и укажите какой бренд вам нужен!', show_alert=True)


async def callback_for_cancel_typing_feedback_btn(query: types.CallbackQuery):
    if User.get_by_id(query.from_user.id).state != 'TYPING FEEDBACK':
        await query.answer('Вы сейчас не отправляете сообщение обратной связи!', show_alert=True)
        await query.message.delete()
        return
    if User.get_by_id(query.from_user.id).id_of_message_promoter_to_type != query.message.message_id:
        await query.answer('Вы нажали на кнопку из другого сообщения!', show_alert=True)
        await query.message.delete()
        return
    User.get_by_id(query.from_user.id).state = 'NONE'
    await query.answer(f'Написание сообщения обратной сваязи отменено!', show_alert=True)
    await query.message.delete()


async def problem_with_username(query: types.CallbackQuery):
    await query.message.answer(
        'Извините, но я не могу с вами работать, т. к. у вас нету имени пользователя в Telegram!\nПожалуйста добавьте имя полльзователя в настройках профиля и приходите обратно!\nСпасибо за понимание!')
    await query.answer()


async def callback_for_page_number_button(query: types.CallbackQuery):
    await query.answer(
        f'Вы находитесь на странице №{query.message.reply_markup.inline_keyboard[-3][1].text.split(" / ")[0]} из {query.message.reply_markup.inline_keyboard[-3][1].text.split(" / ")[1]}')


async def callback_for_goto_brands_page_buttons(query: types.CallbackQuery):
    new_page_n = int(query.data.split()[-1])
    search_query = query.message.text.split('"')[-2]
    result = SparePart.search(search_query)
    if new_page_n == 0:
        await query.answer('Вы находитесь на первой странице!', True)
        return
    if new_page_n - result.brands_pages_count == 1:
        await query.answer('Вы находитесь на последней странице странице!', True)
        return
    if new_page_n > result.brands_pages_count:
        new_page_n = Brand.pages_count()
    await query.message.edit_reply_markup(reply_markup=result.brands_pages_keyboard(new_page_n))


async def not_registered(query: types.CallbackQuery):
    await query.answer('Вы не зарегистрированы, чтобы это сделать напишите мне любое сообщение!', True)


async def callback_for_back_to_brands_button(query: types.CallbackQuery):
    page_n = int(query.data.split()[-1])
    search_query = query.message.text.split('"')[-2]
    result = SparePart.search(search_query)
    text = f'Найдено {result.spare_parts_count} запчаст{"ь" if result.spare_parts_count == 1 else "и"} {len(result.brands)} бренд{"а" if len(result.brands) == 1 else "ов"} по запросу "{search_query}":' if result.spare_parts_count > 0 else f'Не найдено запчастей по запросу "{search_query}"!'
    await query.message.edit_text(text, reply_markup=result.brands_pages_keyboard(page_n))


async def send_contact(query: types.CallbackQuery):
    await query.answer(User.get_by_id(query.from_user.id).end_type_text)
    markup = types.ReplyKeyboardMarkup(inline_keyboard=[[types.KeyboardButton(text='Поделиться', request_contact=True)]],
                                       resize_keyboard=True)
    await query.message.answer(User.get_by_id(query.from_user.id).end_type_text, reply_markup=markup)


def reg_handlers():
    dp.callback_query.register(problem_with_username, lambda query: query.from_user.username is None)
    dp.callback_query.register(not_registered, lambda query: not User.is_id_registered(query.from_user.id))
    dp.callback_query.register(send_contact, lambda query: User.get_by_id(query.from_user.id).state == 'SENDING CONTACT')
    dp.callback_query.register(callback_for_help_typing_query_btn, F.data == 'HELP TYPING QUERY')
    dp.callback_query.register(callback_for_cancel_typing_query_btn, F.data == 'CANCEL TYPING QUERY')
    dp.callback_query.register(callback_for_search_something_btn,
                                       lambda query: query.data.startswith('SEARCH "'))
    dp.callback_query.register(callback_for_cancel_typing_feedback_btn, F.data == 'CANCEL TYPING FEEDBACK')
    dp.callback_query.register(callback_for_start_btn,
                                       lambda query: query.data.startswith('SEARCH'))
    dp.callback_query.register(callback_for_goto_sp_page_buttons,
                                       lambda query: query.data.startswith('GOTO SP PAGE '))
    dp.callback_query.register(callback_for_goto_brands_page_buttons,
                                       lambda query: query.data.startswith('GOTO BRANDS PAGE '))
    dp.callback_query.register(callback_for_page_number_button, F.data == 'PAGE NUMBER')
    dp.callback_query.register(callback_for_contacts_btn, F.data == 'CONTACTS')
    dp.callback_query.register(callback_for_need_new_brand_btn, F.data == 'NEED NEW BRAND')
    dp.callback_query.register(callback_for_choose_brand_buttons,
                                       lambda query: query.data.startswith('CHOOSE BRAND "'))
    dp.callback_query.register(callback_for_show_spare_part_btns,
                                       lambda query: query.data.startswith('SHOW '))
    dp.callback_query.register(callback_for_back_to_brands_button,
                                       lambda query: query.data.startswith('BACK TO BRANDS '))
