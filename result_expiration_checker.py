import asyncio
from datetime import datetime, UTC
from aiogram import types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from classes import Query
from create_bot import bot


async def check_expiration():
    queries = Query.get_all()
    for query in queries:
        if query.expiration_datetime < datetime.now(UTC) and query.get_result:
            # query.get_result = None
            try:
                await bot.edit_message_text(f'Результаты запроса "{query.text}" устарели, пожалуйста, обновите их!',
                                            query.from_user_id,
                                            query.message_id,
                                            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                                [types.InlineKeyboardButton(text='Обновить',
                                                                            callback_data='RELOAD RESULTS')],
                                                [types.InlineKeyboardButton(text='Ввести другой запрос',
                                                                            callback_data='SEARCH AND DELETE CALL.MESSAGE')]]))
            except: ...


def schedule_all(scheduler: AsyncIOScheduler):
    scheduler.add_job(check_expiration, trigger='cron', minute="*/1")


def main():
    scheduler = AsyncIOScheduler()
    schedule_all(scheduler)
    scheduler.start()
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
