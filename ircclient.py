import socket
from functools import reduce
import logging
import re

def send(c, u, msg):
    c.bot.send_message(chat_id=u.effective_chat.id,
                       text=msg, parse_mode='Markdown')

from users import UsersList
users = UsersList()

class IrcClient():
    def __init__(self, host='', port=6667, name="botty", channel="#lobby"):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        client.send(f"NICK {name}\r\n \
                     USER {name} 0 * :{name}\r\n \
                     JOIN {channel}\r\n \
                     PRIVMSG NickServ :set always-on truer\n".encode())
        self.host = host
        self.port = port
        self.channel = channel
        self.name = name
        self.client = client
        self.lastMessageId = None

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

    def recv(self, n=1):
        """
        This is a work in progress... pass in a number like 3 or 4 and send some messages
        """


        IRC_P = {
            r'^:(.*)!.*PRIVMSG (.*) :(.*)$': lambda g: {"nick": g.group(1), "channel": g.group(2), "text": g.group(3)},
            r'^\s*PING \s*' + self.name + r'\s*$': lambda g: {"ping": self.name},
            r'^:.* 353 '+self.name+r' = '+self.channel+r' :(.*)\s*$': lambda g: {"names": g.group(1).split()},
            r'^:.* 322 '+self.name+r' (.+) 1 :(.+)\s*$': lambda g: {"channel": g.group(1), "chandescription": g.group(2)},
            r'^:(.+)!.* QUIT :(.*)\s*$': lambda g:{'reply': f"`{g[1]}` has quit  {g[2]}"},
            r'^:(.+)!.* JOIN (\S+)\s*$': lambda g:{'reply':  f"`{g[1]}` has joined  {g[2]}"},
            r'^:(.+)!.* PART (\S+)\s*$': lambda g:{'reply':  f"`{g[1]}` has left  {g[2]}"},
            r'^:(.+) 433 (\S*) (\S*) :(.*)\s*$': lambda g:{'reply':  f"*{g[1]}*"},
            r'^:'+self.name+'!.* QUIT (.*)\s*$': lambda g:{'reply':  f"*{g[1]}: You have quit*"},
            r'^:'+self.name+'!.* NICK (\S+)\s*$': lambda g:{'nickchange': g[1], 'reply': f"*You are now known as {g[1]}*"},
        } 
        return list(
            map(lambda g: IRC_P[g.re.pattern](g),
                filter(lambda m: m,
                       map(lambda m: reduce(lambda x, y: x or y, [re.match(reg, m) for reg in IRC_P]),
                           reduce(lambda x, y: x+y,
                                  [self.client.recv(4096).decode('utf-8').split("\r\n") for i in range(n)])
                           )
                       )
                )
        )


def fetch_irc_updates(c):
    global users
    remove = []
    for id in users:
        try:
            client = users[id]
            msgs = client.recv()
            for msg in msgs:
                if "nickchange" in msg:
                    client.name = msg["nickchange"]
                if 'ping' in msg:
                    client.send_raw("PONG " + client.host)
                    logging.info("Ping request: PONGING")
                elif 'names' in msg:
                    text = f"*{client.channel}*\n\n"
                    for n in msg['names']:
                        text += "`"+n+"    `"
                    c.bot.send_message(chat_id=id, text=text,
                                       parse_mode='Markdown')
                elif "chandescription" in msg:
                    text = f"*{msg['channel']}:* {msg['chandescription']}"
                    c.bot.send_message(chat_id=id, text=text,
                                       parse_mode='Markdown')
                elif "reply" in msg:
                    c.bot.send_message(chat_id=id, text=msg['reply'],
                                       parse_mode='Markdown')
                else:
                    logging.info(client.lastMessageId)
                    if client.name in msg['text'] and client.lastMessageId:
                        logging.info("--000000000000000000000000000000-- REPLYING")
                        c.bot.send_message(chat_id=id, text=f"*{msg['nick']}:* {msg['text']}",
                                           parse_mode='Markdown', reply_to_message_id=client.lastMessageId)
                    else:
                        c.bot.send_message(
                            chat_id=id, text=f"*{msg['nick']}:* {msg['text']}", parse_mode='Markdown')
        except Exception as e:
            c.bot.send_message(
                chat_id=id, text=f"*You were disconected:* "+str(e), parse_mode='Markdown')
            remove.append(id)
    for i in remove:
        try:
            del users[id]
            users[id].close()
        except:
            pass


def ircJoin(u, c, host, port=6667, channel='#lobby'):
    c.user_data['host'] = host
    c.user_data['port'] = port
    channel = c.user_data['channel'] = channel
    nick = c.user_data['nick'] = "TG-"+u.message.from_user.first_name
    c.user_data['id'] = u.message.from_user.id
    logging.info("Connecting")
    try:
        logging.info(
            f"Host: {host}:{port} with nick {nick} on channel {channel}")
        users[c.user_data['id']] = IrcClient(host, port, nick, channel)
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


