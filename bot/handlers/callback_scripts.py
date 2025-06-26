from aiogram.enums import ChatAction
from aiogram import types, F, Router

from classes import SingleQuery, SparePart, User, Photo, Brand, SearchResult, AnalogSearchResult, AccessRequest
from classes.access_request import ResponseException
from classes.multiquery import MultiQuery
from config import text_of_contacts_message
from bot.create_bot import bot
from bot.filters import StateFilter
from bot.keyboards import query_keyboard
from bot.query_utils import get_query_text
from utils import morph


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
    brand_n = int(query.data.split()[-1])
    if new_page_n < 0:
        await query.answer('Вы находитесь на первой странице!', True)
        return
    if new_page_n >= result.pages_count_of_brand(brand_n):
        await query.answer('Вы находитесь на последней странице странице!', True)
        return
    await query.message.edit_reply_markup(reply_markup=result.sp_pages_of_brand_keyboard(brand_n, new_page_n))


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


async def callback_for_show_spare_part_buttons(query: types.CallbackQuery, user: User):
    await query.answer()
    await bot.send_chat_action(query.from_user.id, ChatAction.TYPING)
    n = int(query.data.split()[-1])
    brand_n = int(query.data.split()[-2])
    query_text = get_query_text(query.message)
    result = await SearchResult.get(query_text)
    sp = await result.spare_parts[result.brands_uids_list[brand_n]][n].get_full_info()
    await sp.send_info_to_user(user)


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
    brand_n = int(query.data.split(' ')[-1])
    query_text = get_query_text(query.message)
    result = await SearchResult.get(query_text)
    await query.message.edit_text(
        f'Запрос: <code>{query_text}</code>\n\n' + result.get_result_stats_text_for_brand(brand_n),
        parse_mode='HTML',
        reply_markup=result.sp_pages_of_brand_keyboard(brand_n, 0))


async def callback_for_start_button(query: types.CallbackQuery, user: User):
    if user.state != 'NONE':
        await query.answer(user.end_type_text, True)
        return
    await query.answer()
    from bot.handlers.text_scripts import search
    await search(query.message, user)


async def callback_for_need_new_brand_btn(query: types.CallbackQuery):
    await query.answer('Напишите об этом в обратной связи и укажите какой бренд вам нужен!', show_alert=True)


async def callback_for_cancel_typing_feedback_btn(query: types.CallbackQuery, user: User):
    user.state = 'NONE'
    await query.answer(f'Написание сообщения обратной связи отменено!', show_alert=True)
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
    if new_page_n < 0:
        await query.answer('Вы находитесь на первой странице!', True)
        return
    if new_page_n >= result.brands_pages_count:
        await query.answer('Вы находитесь на последней странице странице!', True)
        return
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

async def callback_for_show_analog_sp_buttons(query: types.CallbackQuery, user: User):
    await query.answer()
    n = int(query.data.split()[-1])
    code = query.message.text.split('\n')[1].split()[-1]
    res = await AnalogSearchResult.get_by_code(code)
    if not res:
        await query.message.delete_reply_markup()
        await query.message.edit_text('Запчасть, для которой вы искали аналоги не найдена!')
        return
    if len(res.analogs) <= n:
        await query.message.delete_reply_markup()
        await query.message.edit_text('Произошла ошибка, попробуйте поискать аналоги для этой запчасти ещё раз!')
        return
    sp = await res.analogs[n].get_full_info()
    await sp.send_info_to_user(user)

async def callback_for_goto_asp_page_buttons(query: types.CallbackQuery):
    new_page_n = int(query.data.split()[-1])
    code = query.message.text.split('\n')[1].split()[-1]
    res = await AnalogSearchResult.get_by_code(code)
    if not res:
        await query.answer()
        await query.message.delete_reply_markup()
        await query.message.edit_text('Запчасть, для которой вы искали аналоги не найдена!')
        return
    if new_page_n < 0:
        await query.answer('Вы находитесь на первой странице', True)
    elif new_page_n >= res.pages_count:
        await query.answer('Вы находитесь на последней странице', True)
    else:
        await query.answer()
    new_page_n = max(0, min(new_page_n, res.pages_count - 1))
    await query.message.edit_reply_markup(reply_markup=res.keyboard(new_page_n))


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

async def callback_for_accept_reg_button(query: types.CallbackQuery, user: User):
    request = AccessRequest.get_by_id(int(query.data.split()[-1]))
    request_message_id = User.get_by_id(request.user_id).id_of_message_promoter_to_type
    try:
        request.accept(user.id)
    except ResponseException:
        await query.answer(
            "Запрос уже, принят, отклонён или отменён отправителем! Чтобы узнать подробнее, обновите информацию!", True)
        return
    reg_user = User.get_by_id(request.user_id)
    await query.answer('Запрос принят успешно!', True)
    await query.message.delete()
    await query.message.answer(f'Вы приняли запрос доступа к боту от <code>{reg_user.phone}</code>', parse_mode="HTML")
    await reg_user.send_message('Ваш запрос на регистрацию был принят!')
    await reg_user.send_message(
        f'Здравствуйте {query.from_user.full_name}!\nЯ бот компании ООО "ОМ партс", которая входит в группу компаний ТД "Овоще-молочный", помогу вам с лёгкостью найти любую запчасть, если она есть в нашей базе данных!\n\n{"" if user.phone != "" else "Пожалуйста, поделись со мной своим контактом Telegram с помощью кнопки ниже, чтобы я занёс ваш номер в свою базу данных, если вы не хотите чтобы я хранил ваш номер, то, к сожалению, вы не сможете использовать этого бота!"}')
    await bot.delete_message(reg_user.id, request_message_id)


async def callback_for_reject_reg_button(query: types.CallbackQuery, user: User):
    request = AccessRequest.get_by_id(int(query.data.split()[-1]))
    reg_user = User.get_by_id(request.user_id)
    try:
        request.reject(user.id)
    except ResponseException:
        await query.answer(
            "Запрос уже, принят, отклонён или отменён отправителем! Чтобы узнать подробнее, обновите информацию!", True)
        return
    await query.answer('Запрос отклонён успешно!', True)
    await query.message.delete()
    await reg_user.delete_state_message()
    await query.message.answer(f'Вы отклонили запрос доступа к боту от {reg_user.phone}')
    await reg_user.send_message('Ваш запрос на регистрацию был отклонён!')


async def callback_for_ban_reg_button(query: types.CallbackQuery, user: User):
    request = AccessRequest.get_by_id(int(query.data.split()[-1]))
    reg_user = User.get_by_id(request.user_id)
    try:
        request.reject_and_ban(user.id)
    except ResponseException:
        await query.answer("Запрос уже, принят, отклонён или отменён отправителем! Чтобы узнать подробнее, обновите информацию!", True)
        return
    await query.answer('Запрос отклонён успешно!', True)
    await query.message.delete()
    await query.message.answer(
        f'Вы отклонили запрос доступа к боту от {reg_user.phone}\nВы успешно заблокировали исходящие запросы от {reg_user.phone}\nID: {reg_user.id}\nЧто бы разблокировать напишите команду /unban')
    await reg_user.delete_state_message()
    await reg_user.send_message(
        f'Ваш запрос на регистрацию был отклонён! Вы были заблокированы для разблокировки передайте ваш ID руководству\nID: {reg_user.id}')


async def callback_for_update_requests_button(query: types.CallbackQuery, user: User):
    requests = AccessRequest.get_waiting()
    try:
        await query.message.edit_text(f'<b>{len(requests)}</b> {morph.parse("запрос")[0].make_agree_with_number(len(requests)).word}, ожидающих ответа',
                             reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=request.user_phone, callback_data=f'VIEW REQUEST {request.id}')] for request in requests] + [[types.InlineKeyboardButton(text="↻ Обновить", callback_data="UPDATE REQUESTS")]]),
                             parse_mode='HTML')
    except:
        await query.answer("Данные обновлены")
    else:
        await query.answer()


async def callback_for_view_request_buttons(query: types.CallbackQuery):
    request = AccessRequest.get_by_id(int(query.data.split()[-1]))
    try:
        await query.message.edit_text(await request.get_info(False), reply_markup=request.responding_keyboard(),
                                      parse_mode='HTML')
    except:
        await query.answer("Данные обновлены")
    else:
        await query.answer()


callback_queries_router = Router(name='callback_queries')
callback_queries_router.callback_query.register(problem_with_username, lambda query: query.from_user.username is None)
callback_queries_router.callback_query.register(not_registered, lambda _, user_exists: not user_exists)
callback_queries_router.callback_query.register(send_contact, lambda _, user: user.state == 'SENDING CONTACT')
callback_queries_router.callback_query.register(callback_for_help_typing_query_btn, F.data == 'HELP TYPING QUERY', flags={
        'state_filter': StateFilter("TYPING QUERY", True),
        "check_state_message": True,
        "state_error_message": 'Вы сейчас не отправляете запрос!'
    })
callback_queries_router.callback_query.register(callback_for_cancel_typing_query_btn, F.data == 'CANCEL TYPING QUERY', flags={
        'state_filter': StateFilter("TYPING QUERY", True),
        "check_state_message": True,
        "state_error_message": 'Вы сейчас не отправляете запрос!'
    })
callback_queries_router.callback_query.register(callback_for_set_query_type_button,
                           lambda query: query.data.startswith('SET_QUERY_TYPE '), flags={
        'state_filter': StateFilter("TYPING QUERY", True),
        "check_state_message": True,
        "state_error_message": 'Вы сейчас не отправляете запрос!'
    })
# callback_queries_router.callback_query.register(callback_for_search_something_btn,
#                            lambda query: query.data.startswith('SEARCH "'), flags={
#         'state_filter': StateFilter("TYPING QUERY"),
#         "check_state_message": True,
#         'state_error_message': 'Вы сейчас не отправляете запрос!'
#     })
callback_queries_router.callback_query.register(callback_for_cancel_typing_feedback_btn, F.data == 'CANCEL TYPING FEEDBACK', flags={
    'state_filter': StateFilter("TYPING FEEDBACK"),
    "check_state_message": True,
    "state_error_message": 'Вы сейчас не отправляете сообщение обратной связи!'
})
# callback_queries_router.callback_query.register(callback_for_reload_results_button, F.data == 'RELOAD RESULTS')
callback_queries_router.callback_query.register(callback_for_start_button,
                           lambda query: query.data.startswith('SEARCH'))
callback_queries_router.callback_query.register(callback_for_goto_sp_page_buttons,
                           lambda query: query.data.startswith('GOTO SP PAGE '))
callback_queries_router.callback_query.register(callback_for_goto_asp_page_buttons,
                           lambda query: query.data.startswith('GOTO ASP PAGE '))
callback_queries_router.callback_query.register(callback_for_goto_brands_page_buttons,
                           lambda query: query.data.startswith('GOTO BRANDS PAGE '))
callback_queries_router.callback_query.register(callback_for_page_number_button, lambda query: query.data.startswith('PAGE NUMBER'))
callback_queries_router.callback_query.register(callback_for_contacts_btn, F.data == 'CONTACTS')
callback_queries_router.callback_query.register(callback_for_need_new_brand_btn, F.data == 'NEED NEW BRAND')
callback_queries_router.callback_query.register(callback_for_choose_brand_buttons,
                           lambda query: query.data.startswith('CHOOSE BRAND '))
callback_queries_router.callback_query.register(callback_for_show_spare_part_buttons,
                           lambda query: query.data.startswith('SHOW SP '))
callback_queries_router.callback_query.register(callback_for_show_analog_sp_buttons,
                           lambda query: query.data.startswith('SHOW ASP '))
callback_queries_router.callback_query.register(callback_for_back_to_brands_button,
                           lambda query: query.data.startswith('BACK TO BRANDS '))
callback_queries_router.callback_query.register(callback_for_export_mq_to_excel_button,
                           lambda query: query.data.startswith('EXPORT MQ XLSX '))
callback_queries_router.callback_query.register(callback_for_accept_reg_button,
                               lambda query: query.data.startswith('ACCEPT REG '),
                               flags={"required_permissions": ["responder"]})
callback_queries_router.callback_query.register(callback_for_reject_reg_button,
                               lambda query: query.data.startswith('REJECT REG '),
                               flags={"required_permissions": ["responder"]})
callback_queries_router.callback_query.register(callback_for_ban_reg_button,
                                   lambda query: query.data.startswith('REJECT AND BAN REG '),
                                   flags={"required_permissions": ["responder"]})
callback_queries_router.callback_query.register(callback_for_update_requests_button,
                               F.data == 'UPDATE REQUESTS',
                               flags={"required_permissions": ["responder"]})
callback_queries_router.callback_query.register(callback_for_view_request_buttons,
                               lambda query: query.data.startswith('VIEW REQUEST '),
                               flags={"required_permissions": ["responder"]})
