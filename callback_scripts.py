from aiogram.enums import ChatAction
from aiogram import types, F
from classes import SingleQuery, SparePart, User, Photo, Brand, SearchResult
from classes.multiquery import MultiQuery
from config import text_of_contacts_message
from create_bot import dp, bot
from filters import StateFilter
from keyboards import query_keyboard
from query_utils import get_query_text


# async def callback_for_search_something_btn(query: types.CallbackQuery, user: User):
#     await query.message.edit_text('Запрос обрабатывается, это займёт меньше минуты...')
#     user.state = 'NONE'
#     search_query = SingleQuery.create(query.from_user.id, query.data.split('"')[-2], query.message.message_id)
#     result = await search_query.get_result()
#     text = f'Запрос: <code>{query_text}</code>\n\n' + result.get_result_stats_text()
#     await query.message.edit_text(text, reply_markup=result.brands_pages_keyboard(1))


async def callback_for_goto_sp_page_buttons(query: types.CallbackQuery):
    query_text = get_query_text(query.message)
    result = await SearchResult.get(query_text)
    new_page_n = int(query.data.split()[-2])
    if new_page_n == 0:
        await query.answer('Вы находитесь на первой странице!', True)
        return
    if new_page_n - result.pages_count_of_brand(query.data.split('"')[-2]) == 1:
        await query.answer('Вы находитесь на последней странице странице!', True)
        return
    if new_page_n > result.pages_count_of_brand(query.data.split('"')[-2]):
        new_page_n = result.pages_count_of_brand(query.data.split('"')[-2])
    await query.message.edit_reply_markup(reply_markup=result.sp_pages_of_brand_keyboard(query.data.split('"')[-2], new_page_n))


# async def callback_for_back_to_results_btn(query: types.CallbackQuery):
#     search_query = query.message.caption.split('"')[1]
#     brand = 'KUHN' if 'KUHN' in query.message.caption.split('\n')[1] else 'DIECI' if 'DIECI' in query.message.caption.split('\n')[1] else 'CNHi'
#     results = SparePart.search(search_query, brand)
#     text = f'Найденн{"ая" if len(results) == 1 else "ые"} запчаст{"ь" if len(results) == 1 else "и"} бренда {brand.name} по запросу "{search_query}":' if len(
#         results) > 0 else f'Не найдено запчастей бренда {brand.name} по запросу "{search_query}"!'
#     markup = types.InlineKeyboardMarkup(1)
#     for result in results:
#         markup.add(
#             types.InlineKeyboardButton(text=result.name, callback_data=f'SHOW "{result.code}"'))
#     markup.add(types.InlineKeyboardButton(text='Поискать у других компаний', callback_data='SEARCH AND DELETE CALL.MESSAGE'))
#     markup.add(types.InlineKeyboardButton(text=f'Ввести другой запрос по бренду {brand.name}',
#                                           callback_data=f'CHOOSE BRAND "{brand.uid}"'))

# await query.message.answer(text, reply_markup=markup)
# await query.message.delete()


async def callback_for_show_spare_part_btns(query: types.CallbackQuery):
    await query.answer()
    await bot.send_chat_action(query.from_user.id, ChatAction.TYPING)
    n = int(query.data.split()[-1])
    query_text = get_query_text(query.message)
    result = await SearchResult.get(query_text)
    sp = await result.spare_parts[n].get_full_info()
    text = f'Запрос: <code>{query_text}</code>.\nБренд: <code>{sp.brand.name}</code>\nНаименование: <code>{sp.name}</code>\nАртикул: <code>{sp.code}</code>\n\n'
    if sp.counts:
        text += 'В наличии:\n'
    else:
        text += 'Нет в наличии.'
    for count in sp.counts:
        text += f"{count}\n"
    try:
        if len(sp.photos) == 1:
            await query.message.answer_photo(types.FSInputFile(sp.photos[0].download()), text, parse_mode='HTML')
        elif len(sp.photos) == 0:
            await query.message.answer(text, parse_mode='HTML')
        else:
            media_list = []
            for i, photo in enumerate(sp.photos):
                if i == 0:
                    media_list.append(
                        types.InputMediaPhoto(media=types.FSInputFile(photo.download()), caption=text, parse_mode='HTML'))
                    continue
                media_list.append(types.InputMediaPhoto(media=types.FSInputFile(photo.download())))
            await query.message.answer_media_group(media=media_list)
    except Exception as e:
        await query.message.answer(text + '\n\nОшибка, недопустимый размер изображения! Изображение не подгружено!\n\n' + str(e),
                                   parse_mode='HTML')
    for photo in sp.photos:
        photo.remove()


async def callback_for_cancel_typing_query_btn(query: types.CallbackQuery, user: User):
    user.state = 'NONE'
    await query.message.edit_text('Поиск отменён!', reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='Искать запчасти!', callback_data='SEARCH')]]))
    await query.answer('Поиск отменён!')


async def callback_for_help_typing_query_btn(query: types.CallbackQuery, user: User):
    await query.answer('Введите артикул или часть наименования запчасти, которую вы ищите!', show_alert=True)


async def callback_for_set_query_type_button(query: types.CallbackQuery, user: User):
    new_type: str = query.data.split(' ')[-1]
    user.state = f"TYPING QUERY {new_type}"
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=query_keyboard(user, new_type))


async def callback_for_contacts_btn(query: types.CallbackQuery):
    await query.message.answer(text_of_contacts_message)


async def callback_for_choose_brand_buttons(query: types.CallbackQuery):
    brand_uid = query.data.split('"')[-2]
    query_text = get_query_text(query.message)
    result = await SearchResult.get(query_text)
    await query.message.edit_text(
        f'Запрос: <code>{query_text}</code>\n\n' + result.get_result_stats_text_for_brand(brand_uid),
        parse_mode='HTML',
        reply_markup=result.sp_pages_of_brand_keyboard(brand_uid, 1))


async def callback_for_start_btn(query: types.CallbackQuery, user: User):
    if user.state != 'NONE':
        await query.answer(user.end_type_text, True)
        return
    await query.answer()
    from text_scripts import search
    await search(query.message, user)


async def callback_for_need_new_brand_btn(query: types.CallbackQuery):
    await query.answer('Напишите об этом в обратой связи и укажите какой бренд вам нужен!', show_alert=True)


async def callback_for_cancel_typing_feedback_btn(query: types.CallbackQuery, user: User):
    user.state = 'NONE'
    await query.answer(f'Написание сообщения обратной сваязи отменено!', show_alert=True)
    await query.message.delete()


async def problem_with_username(query: types.CallbackQuery):
    await query.message.answer(
        'Извините, но я не могу с вами работать, т. к. у вас нету имени пользователя в Telegram!\nПожалуйста добавьте имя полльзователя в настройках профиля и приходите обратно!\nСпасибо за понимание!')
    await query.answer()


async def callback_for_page_number_button(query: types.CallbackQuery):
    await query.answer(
        f'Вы находитесь на странице №{query.message.reply_markup.inline_keyboard[-1][1].text.split(" / ")[0]} из {query.message.reply_markup.inline_keyboard[-1][1].text.split(" / ")[1]}')


async def callback_for_goto_brands_page_buttons(query: types.CallbackQuery):
    new_page_n = int(query.data.split()[-1])
    query_text = get_query_text(query.message)
    result = await SearchResult.get(query_text)
    if new_page_n == 0:
        await query.answer('Вы находитесь на первой странице!', True)
        return
    if new_page_n - result.brands_pages_count == 1:
        await query.answer('Вы находитесь на последней странице странице!', True)
        return
    if new_page_n > result.brands_pages_count:
        new_page_n = result.brands_pages_count
    await query.message.edit_reply_markup(reply_markup=result.brands_pages_keyboard(new_page_n))


async def not_registered(query: types.CallbackQuery):
    await query.answer('Вы не зарегистрированы, чтобы это сделать напишите мне любое сообщение!', True)


async def callback_for_back_to_brands_button(query: types.CallbackQuery):
    page_n = int(query.data.split()[-1])
    query_text = get_query_text(query.message)
    result = await SearchResult.get(query_text)
    text = f'Запрос: <code>{query_text}</code>\n\n' + result.get_result_stats_text()
    await query.message.edit_text(text,
        parse_mode='HTML', reply_markup=result.brands_pages_keyboard(page_n))


async def send_contact(query: types.CallbackQuery, user: User):
    await query.answer(user.end_type_text)
    markup = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text='Поделиться', request_contact=True)]],
        resize_keyboard=True)
    await query.message.answer(user.end_type_text, reply_markup=markup)


# async def callback_for_reload_results_button(query: types.CallbackQuery):
#     search_query = Query.get_by_from_user_id_and_message_id(query.from_user.id, query.message.message_id)
#     await query.message.edit_text("Результаты обновляются, пожалуйста, подождите, это займёт меньше минуты...")
#     result = await search_query.get_result()
#     text = f'Найдено {len(result.spare_parts)} запчаст{"ь" if len(result.spare_parts) == 1 else "и"} {len(result.brands)} бренд{"а" if len(result.brands) == 1 else "ов"} по запросу "{search_query.text}":' if len(result.spare_parts) > 0 else f'Не найдено запчастей по запросу "{search_query.text}"!'
#     await query.message.edit_text(text, reply_markup=result.brands_pages_keyboard(1))

async def callback_for_export_mq_to_excel_button(query: types.CallbackQuery, user: User):
    mq = MultiQuery.get_by_id(int(query.data.split()[-1]))
    await bot.send_chat_action(user.id, 'upload_document')
    await mq.export_results_to_excel()
    await query.message.answer_document(types.FSInputFile('result.xlsx',
                                                          f'Мультизапрос #{mq._id}.xlsx'))


def reg_handlers():
    dp.callback_query.register(problem_with_username, lambda query: query.from_user.username is None)
    dp.callback_query.register(not_registered, lambda _, user_exists: not user_exists)
    dp.callback_query.register(send_contact, lambda _, user: user.state == 'SENDING CONTACT')
    dp.callback_query.register(callback_for_help_typing_query_btn, F.data == 'HELP TYPING QUERY', flags={
            'state_filter': StateFilter("TYPING QUERY", True),
            "check_state_message": True,
            "state_error_message": 'Вы сейчас не отправляете запрос!'
        })
    dp.callback_query.register(callback_for_cancel_typing_query_btn, F.data == 'CANCEL TYPING QUERY', flags={
            'state_filter': StateFilter("TYPING QUERY", True),
            "check_state_message": True,
            "state_error_message": 'Вы сейчас не отправляете запрос!'
        })
    dp.callback_query.register(callback_for_set_query_type_button,
                               lambda query: query.data.startswith('SET_QUERY_TYPE '), flags={
            'state_filter': StateFilter("TYPING QUERY", True),
            "check_state_message": True,
            "state_error_message": 'Вы сейчас не отправляете запрос!'
        })
    # dp.callback_query.register(callback_for_search_something_btn,
    #                            lambda query: query.data.startswith('SEARCH "'), flags={
    #         'state_filter': StateFilter("TYPING QUERY"),
    #         "check_state_message": True,
    #         'state_error_message': 'Вы сейчас не отправляете запрос!'
    #     })
    dp.callback_query.register(callback_for_cancel_typing_feedback_btn, F.data == 'CANCEL TYPING FEEDBACK', flags={
        'state_filter': StateFilter("TYPING FEEDBACK"),
        "check_state_message": True,
        "state_error_message": 'Вы сейчас не отправляете сообщение обратной связи!'
    })
    # dp.callback_query.register(callback_for_reload_results_button, F.data == 'RELOAD RESULTS')
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
    dp.callback_query.register(callback_for_export_mq_to_excel_button,
                               lambda query: query.data.startswith('EXPORT MQ XLSX '))
