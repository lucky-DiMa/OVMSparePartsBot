import asyncio
import logging
from datetime import datetime
from random import randint
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from icecream import ic
from api import app as api_app
from bot.middleware import register_middleware
from config import BY_WEBHOOK, BASE_WEBHOOK_URL
from bot.create_bot import dp, bot
from utils import connect_redis, close_redis
from bot.handlers import router

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 5004
WEBHOOK_PATH = "/webhook2"
WEBHOOK_SECRET = str(randint(1, 1000000))


async def on_startup_webhook() -> None:
    await connect_redis()
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)

async def on_shutdown() -> None:
    await close_redis()


def start_bot_webhook() -> None:
    dp.startup.register(on_startup_webhook)
    dp.shutdown.register(on_shutdown)
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.add_subapp('/webhook2/api', api_app)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

async def on_startup_polling():
    await connect_redis()

async def start_bot_polling():
    await bot.delete_webhook()
    dp.startup.register(on_startup_polling)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


def main():
    if BY_WEBHOOK:
        start_bot_webhook()
    else:
        asyncio.run(start_bot_polling())


if __name__ == "__main__":
    if BY_WEBHOOK:
        logging.basicConfig(filename='LOG.log')
        logging.log(level=logging.INFO, msg=f'STARTED GMT +0 "{datetime.now()}"')
        ic.disable()
    register_middleware(dp)
    dp.include_router(router)
    main()
