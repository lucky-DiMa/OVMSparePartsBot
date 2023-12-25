import callback_scripts, text_scripts, middleware


def register_handlers():
    middleware.register_middleware()
    callback_scripts.reg_handlers()
    text_scripts.reg_handlers()
