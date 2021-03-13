#!/bin/python3
#TODOS
#refactor so i have a single place to add commands
#add buttons for user PM and for channel join

from env import API_KEY
from ircclient import IrcClient, fetch_irc_updates
from tgcommands import bridge


import logging
from datetime import timedelta

from telegram.ext import MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InlineQueryHandler, PollAnswerHandler, PollHandler, PicklePersistence, Job
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Poll, BotCommand



my_persistence = PicklePersistence(filename='data', store_user_data=True,
                                   store_chat_data=True, store_bot_data=True, single_file=False)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def runTgBot(commands_dict):

    help_msg = ""

    def start(u, c):
        c.bot.send_message(chat_id=u.effective_chat.id, text="""
            Welcome! Get started!""" + "\n\n" + help_msg)

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
    dispatcher.add_handler(echo_handler)
    updater.bot.set_my_commands(descriptions)
    job_queue = updater.job_queue
    job_queue.run_repeating(fetch_irc_updates, timedelta(seconds=1))

    updater.start_polling()
    updater.idle()
