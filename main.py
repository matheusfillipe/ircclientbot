from bot import runTgBot
from ircclient import ircDisconnect
from tgcommands import *

commands_dict = [
    {"cmd": "connect", "func": connect, "desc": "Connects to an IRC server passing the port and ip"},
    {"cmd": "join", "func": join, "desc": "Joins a channel. You can be only in one channel at once"},
    {"cmd": "nick", "func": nick, "desc": "Joins a channel. You can be only in one channel at once"},
    {"cmd": "names", "func": listusers, "desc": "List users in a channel"},
    {"cmd": "list", "func": listchannels, "desc": "List channels in server"},
    {"cmd": "msg", "func": privmsg, "desc": "Start a PM chat with a user"},
    {"cmd": "me", "func": emote, "desc": "Emotes in the chat"},
    {"cmd": "quote", "func": quote, "desc": "Sends a raw command to the server"},
    {"cmd": "imgdel", "func": image_delete, "desc": "Removes image from imgur by passing the url or id. You can only remove images earlier than 48 hours."},
    {"cmd": "status", "func": stats, "desc": "Your current connection information."},
    {"cmd": "save", "func": save, "desc": "Save your current channel and server as a name"},
    {"cmd": "load", "func": load, "desc": "Loads saved channel"},
    {"cmd": "leave", "func": lambda u, c: ircDisconnect(c), "desc": "Disconects from server"},
]


runTgBot(commands_dict)
