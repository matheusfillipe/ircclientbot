

import logging
from datetime import timedelta

from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
                      InlineQueryResultArticle, InputTextMessageContent, Poll)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, Filters, InlineQueryHandler, Job,
                          MessageHandler, PicklePersistence, Updater)

from env import API_KEY
from ircclient import IrcClient, fetch_irc_updates
from tgcommands import bridge, button, image_handler, document_handler

my_persistence = PicklePersistence(filename='data', store_user_data=True,
                                   store_chat_data=True, store_bot_data=True, single_file=False)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def runTgBot(commands_dict):
    help_msg = ""

    def start(u, c):
        c.bot.send_message(chat_id=u.effective_chat.id, text="""
            Welcome! Get started!""" + "\n\n" + help_msg)

    def unknown(u, c):
        c.bot.send_message(chat_id=u.effective_chat.id, text="_Unknown Command!_", parse_mode='Markdown')

    updater = Updater(token=API_KEY,
              persistence=my_persistence, use_context=True)
    dispatcher = updater.dispatcher

    commands_dict = [
        {"cmd": "start", "func": start, "desc": "Shows the Instructions"},
        {"cmd": "help", "func": start, "desc": "Shows the Instructions"},
    ] + commands_dict


    descriptions = []
    for cmd in commands_dict:
        handlers = CommandHandler(cmd['cmd'], cmd['func'])
        dispatcher.add_handler(handlers)
        descriptions.append(BotCommand(cmd['cmd'], cmd['desc']))
        help_msg += f"/{cmd['cmd']}: {cmd['desc']}\n"


    echo_handler = MessageHandler(Filters.text & (~Filters.command), bridge)
    dispatcher.add_handler(MessageHandler(Filters.photo, image_handler))
    dispatcher.add_handler(MessageHandler(Filters.document, document_handler))
    dispatcher.add_handler(MessageHandler(Filters.audio, document_handler))
    dispatcher.add_handler(MessageHandler(Filters.video, document_handler))
    dispatcher.add_handler(MessageHandler(Filters.voice, document_handler))
    dispatcher.add_handler(echo_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.bot.set_my_commands(descriptions)
    aps_logger = logging.getLogger('apscheduler')
    aps_logger.setLevel(logging.ERROR)
    job_queue = updater.job_queue
    job_queue.run_repeating(fetch_irc_updates, timedelta(seconds=.1))

    updater.start_polling()
    updater.idle()
