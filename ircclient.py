import socket
import ssl
from functools import reduce
import logging
import re
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

def send(c, u, msg):
    c.bot.send_message(chat_id=u.effective_chat.id,
                       text=msg, parse_mode='Markdown')

from users import UsersList
from telegram import InlineKeyboardButton
users = UsersList()

class IrcClient():
    def __init__(self, host='', port=6667, name="botty", channel="#lobby", password=None, use_ssl=False):
        if ssl:
            context = ssl.create_default_context()
            sock = socket.create_connection((host, port))
            client = context.wrap_socket(sock, server_hostname=host)
        else:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
        
        terminator = "\r\n"
        client.settimeout(0.2)
        client.send(f"{f'PASS {password}' + terminator if password else ''}\
                     NICK {name}\r\n \
                     USER {name} 0 * :{name}\r\n \
                     JOIN {channel}\r\n \
                     PRIVMSG NickServ :set always-on true\r\n".encode())
        self.host = host
        self.port = port
        self.channel = channel
        self.name = name
        self.nick = name.split("/")[0].replace(":", "")
        self.password = password
        self.ssl = use_ssl
        self.client = client
        self.lastMessageId = None

    def __str__(self):
        return f"host: {self.host}\nport: {self.port}\nnick: {self.name}\nchannel: {self.channel}"

    def send(self, m):
        """
        sends a private message to the channel or user PM if you pass a nickname
        """
        return self.client.send(f"PRIVMSG {self.channel} :{m}\r\n".encode())

    def send_raw(self, m):
        """
        #Use this to implrement more methods: https://tools.ietf.org/html/rfc1459
        """
        return self.client.send(f"{m}\r\n".encode())

    def recv(self):
        """
        Receive irc messages and return list.
        """


        IRC_P = {
            r'^:(.+)!.* PRIVMSG '+self.channel+'\s+:\x01ACTION (.+)\x01$': 
                lambda g:{'reply':  f"*{g[1]} {g[2]}*"},
            r'^:(.*)!.*PRIVMSG (\S+) :(.*)$': lambda g: {"nick": g.group(1), "channel": g.group(2), "text": g.group(3)},
            r'^\s*PING \s*' + self.name + r'\s*$': lambda g: {"ping": self.name},
            r'^\s*PING \s*' + self.nick + r'\s*$': lambda g: {"ping": self.nick},
            r'^\s*PING \s*:(.+)\s*$': lambda g: {"ping": g[1]},
            r'^:\S* 353 '+self.nick+r' = '+self.channel+r' :(.*)\s*$': lambda g: {"names": g.group(1).split()},
            r'^:\S* 322 '+self.nick+r' (\S+) (\d+) :(.+)\s*$': lambda g: {"channel": g.group(1), "chandescription": g.group(3), "count": g[2]},
            r'^:(.+)!.* QUIT :(.*)\s*$': lambda g:{'reply': f"`{g[1]}` has quit  {g[2]}"},
            r'^:(.+)!.* JOIN (\S+)\s*$': lambda g:{'reply':  f"`{g[1]}` has joined  {g[2]}"},
            r'^:(.+)!.* PART (\S+)\s*$': lambda g:{'reply':  f"`{g[1]}` has left  {g[2]}"},
            r'^:(.+) 433 (\S*) (\S*) :(.*)\s*$': lambda g:{'reply':  f"*{g[1]}*"},
            r'^:'+self.nick+'!.* QUIT (.*)\s*$': lambda g:{'reply':  f"*{g[1]}: You have quit*"},
            r'^:'+self.nick+'!.* NICK (\S+)\s*$': lambda g:{'nickchange': g[1], 'reply': f"*You are now known as {g[1]}*"},
        } 
        received = []
        while 1:
            try:
                recv = self.client.recv(4096).decode('utf-8').split("\r\n")
                received.append(recv)
            except socket.timeout:
                break

        if any([any(x) for x in received]):
            print("<<<<", received)
        if received:
            return list(
                map(lambda g: IRC_P[g.re.pattern](g),
                    filter(lambda m: m,
                           map(lambda m: reduce(lambda x, y: x or y, [re.match(reg, m) for reg in IRC_P]),
                               reduce(lambda x, y: x+y, received)
                               )
                           )
                    )
            )
        return []


def fetch_irc_updates(c):
    global users
    remove = []
    for id in users:
        try:
            client = users[id]
            msgs = client.recv()
            for msg in msgs:
                print(">>>>|", str(msg))
                if "nickchange" in msg:
                    client.nick = msg["nickchange"]
                if 'ping' in msg:
                    client.send_raw("PONG " + client.host)
                    logging.info("Ping request: PONGING")
                elif 'names' in msg:
                    button_list = []
                    text = f"*Users on {client.channel}*"
                    i=0
                    for n in msg['names']:
                        if i%2==0:
                            button_list.append([])
                        button_list[-1].append(InlineKeyboardButton(n, callback_data="nick_"+n))
                        i+=1
                    reply_markup = InlineKeyboardMarkup(button_list)
                    c.bot.send_message(chat_id=id, text=text, reply_markup=reply_markup,
                                       parse_mode='Markdown')

                elif "chandescription" in msg:
                    text = f"*{msg['channel']} {msg['count']}:* {msg['chandescription']}"
                    button_list = [[InlineKeyboardButton(msg['channel'], callback_data="channel_"+msg['channel'])]]
                    reply_markup = InlineKeyboardMarkup(button_list)
                    c.bot.send_message(chat_id=id, text=text, reply_markup=reply_markup,
                                       parse_mode='Markdown')
                elif "reply" in msg:
                    c.bot.send_message(chat_id=id, text=msg['reply'],
                                       parse_mode='Markdown')
                else:
                    # Ignore other rooms if messages come from them
                    if 'channel' in msg and msg['channel'] != client.channel:
                        continue
                    msg['text'] = re.sub(r"\003\d\d(?:,\d\d)?", "", msg['text'])
                    if client.nick in msg['text'] and client.lastMessageId:
                        try:
                            c.bot.send_message(chat_id=id, text=f"<b>{msg['nick']}:</b> {msg['text']}",
                                               parse_mode='HTML', reply_to_message_id=client.lastMessageId)
                        except BadRequest:
                            c.bot.send_message(chat_id=id, text=f"{msg['nick']}: {msg['text']}",
                                               reply_to_message_id=client.lastMessageId)
                    else:
                        try:
                            c.bot.send_message(
                                chat_id=id, text=f"<b>{msg['nick']}:</b> {msg['text']}", parse_mode='HTML')
                        except BadRequest:
                            c.bot.send_message(
                                chat_id=id, text=f"{msg['nick']}: {msg['text']}")

        except Exception as e:
                c.bot.send_message(
                    chat_id=id, text=f"*You were disconected:* "+str(e), parse_mode='Markdown')
                remove.append(id)

    for i in remove:
        try:
            users[id].close()
            del users[id]
        except:
            pass


def ircJoin(u, c, host, port=6667, channel='#lobby', nick = None, uid = None, password=None, ssl=False):
    c.user_data['host'] = host
    c.user_data['port'] = port
    c.user_data['password'] = password
    c.user_data['ssl'] = ssl
    channel = c.user_data['channel'] = channel
    nick = c.user_data['nick'] = "TG-"+u.message.from_user.first_name if nick is None else nick
    c.user_data['id'] = u.message.from_user.id if uid is None else uid
    logging.info("Connecting")
    try:
        logging.info(
            f"Host: {host}:{port} with nick {nick} on channel {channel}")
        users[c.user_data['id']] = IrcClient(host, port, nick, channel, password=password, use_ssl=ssl)
        send(c, u, "**Connected!**")
    except Exception as e:
        print("!!!!!!!!!!!!!!!")
        print(e)
        send(c, u, "Unale to connect!")
        try:
            del users[c.user_data['id']]
        except:
            pass


def ircDisconnect(c):
    client = users[c.user_data['id']]
    client.send_raw(f"PART {client.channel}")
    try:
        users[c.user_data['id']].client.close()
    except:
        pass
    try:
        del users[c.user_data['id']]
    except:
        pass


