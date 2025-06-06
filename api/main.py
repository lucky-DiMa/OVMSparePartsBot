from aiohttp import web
from bot import bot
app = web.Application()

router = web.RouteTableDef()

@router.post('/message')
def message(request: web.Request):
    print(request.json())

@router.get('/message')
async def message_get(request: web.Request):
    await bot.send_message(1358414277, 'hi')
    return web.json_response({'status': 200})

app.add_routes(router)