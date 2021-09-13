import logging
import re
from ircclient import ircJoin, ircDisconnect, send
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from env import CLIENT_ID
import pyimgur

from users import UsersList
users = UsersList()

def pastebin(text):
    import requests
    url = "http://ix.io"
    payload={'f:1=<-': text}
    response = requests.request("POST", url, data=payload)
    return response.text


def connect(u, c):
    args = u.message.text.split()[1:]
    if len(args) == 0:
        send(c, u, "Please specify a hostname and a port(defaults to 6667) a nick(default none) and a password(default none)")
        return
    port = int(args[1]) if len(args) > 1 else 6667
    nick = str(args[2]) if len(args) > 2 else None
    password = str(args[3]) if len(args) > 3 else None
    ircJoin(u, c, str(args[0]), port, nick=nick, password=password, ssl=False if port == 6667 else True)


def join(u, c):
    args = u.message.text.split()[1:]
    if len(args) == 0:
        send(c, u, "Please, specify a channel to join")
        return
    channel = c.user_data['channel'] = args[0]
    client = users[c.user_data['id']]
    client.send_raw(f"PART {client.channel}")
    users[c.user_data['id']].channel = c.user_data['channel'] = channel
    client.send_raw(f"JOIN {channel}")
    send(c, u, f"You are now on {channel}")


def emote(u, c):
    args = u.message.text.split()[1:]
    global users
    logging.info("---------------------------------------")
    # or (c.user_data['id'] in users and not users[c.user_data['id']]['on']):
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    if len(args) == 0:
        return
    client = users[c.user_data['id']]
    client.send_raw(f"PRIVMSG {client.channel} :ACTION {' '.join(args)}")


def stats(u, c):
    send(c, u, str(users[c.user_data['id']]))


def save(u, c):
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    args = u.message.text.split()[1:]
    if len(args) == 0:
        send(c, u, "Please, specify a name to save as")
        return
    name = args[0]
    client = users[c.user_data['id']]
    if not 'saved' in c.user_data:
        c.user_data['saved'] = {}
    c.user_data['saved'][name] = {
        'host': client.host, 'name': client.name, 'port': client.port, 'channel': client.channel, 'password': client.password, 'ssl': client.ssl}
    send(c, u, f"Saved {name}!")


def load(u, c):
    args = u.message.text.split()[1:]

    if not 'saved' in c.user_data:
        send(c, u, "You don't have any config saved yet")
        return

    if len(args) == 0:
        i=0
        button_list = []
        for save in c.user_data['saved']:
            obj = c.user_data['saved'][save]
            if i%2==0:
                button_list.append([])
            button_list[-1].append(InlineKeyboardButton(str(save)+": "+"; ".join(
                       [str(obj[k]) for k in obj])[:35], callback_data="load_"+save))
            i+=1
        reply_markup = InlineKeyboardMarkup(button_list)
        id = u.effective_chat.id
        c.bot.send_message(chat_id=id, text= "Please, specify a name to load from. Available ones are:", reply_markup=reply_markup,
                           parse_mode='Markdown')
        return

    name = args[0]
    if not name in c.user_data['saved']:
        send(c, u, "You don't have any save under that name")
        return
    try:
        ircDisconnect(c)
    except:
        pass
    client = c.user_data['saved'][name]
    send(c,u,str({'host': client['host'], 'name': client['name'], 'channel': client['channel']}))
    ircJoin(u, c, client['host'], client['port'], client['channel'], client['name'], password=client['password'], ssl=client['ssl'])


def listusers(u, c):
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    client = users[c.user_data['id']]
    client.send_raw(f"NAMES {client.channel}")
    send(c, u, "*Users on *" + client.channel)


def listchannels(u, c):
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    client = users[c.user_data['id']]
    client.send_raw(f"LIST")
    send(c, u, "*Channels on* " + client.host)


def privmsg(u, c):
    args = u.message.text.split()[1:]
    if len(args) == 0:
        send(c, u, "Please, specify a user on the server to PM to")
        return
    name = args[0]
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    client = users[c.user_data['id']]
    client.send_raw(f"PART {client.channel}")
    users[c.user_data['id']].channel = name
    send(c, u, "*You are now on a PM with* " + client.channel)

def nick(u, c):
    args = u.message.text.split()[1:]
    if len(args) == 0:
        send(c, u, "Please, specify a new nickname")
        return
    name = args[0]
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    client = users[c.user_data['id']]
    client.send_raw(f"NICK {name}")

def bridge(u, c):
    global users
    logging.info("---------------------------------------")
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    try:
        client = users[c.user_data['id']]
        if u.message:
            mt = u.message.text_markdown
            logging.info(mt)
            r = re.match(r'`(.*)`', mt, flags=re.DOTALL)
            logging.info(r)
            if r:
                markdown = r[1]
                url = pastebin(u.message.text)
                client.send(url)
                send(c,u,url)
                return

            msg="    ".join(u.message.text.split("\n"))
            if u.message.reply_to_message:
                reply_to = u.message.reply_to_message.text
                m = re.match(r'^(\S+:) .*$', reply_to)
                if m and m[1]:
                    msg = m[1]+" "+msg
            client.send(msg)
            client.lastMessageId = u.message.message_id
        if u.edited_message:
            msg="    ".join(u.edited_message.text.split("\n"))
            client.send(msg)

    except:
        send(c, u, "You were disconnected! Connect again")
        try:
            del users[c.user_data['id']]
        except:
            pass

def button(u, c):
    query = u.callback_query
    query.answer()
    data = query.data
    args = data.split("_")

    if data.startswith("channel_"):
        client = users[c.user_data['id']]
        client.send_raw(f"PART {client.channel}")
        channel = args[-1]
        users[c.user_data['id']].channel = c.user_data['channel'] = channel
        client.send_raw(f"JOIN {channel}")
        send(c, u, f"You are now on {channel}")

    if data.startswith("nick_"):
        name = args[-1]
        client = users[c.user_data['id']]
        client.send_raw(f"PART {client.channel}")
        users[c.user_data['id']].channel = name
        send(c, u, "*You are now on a PM with* " + client.channel)

    if data.startswith("load_"):
        name = args[-1]
        client = c.user_data['saved'][name]
        send(c,u,str(client))
        ircJoin(u, c, client['host'], client['port'], client['channel'], client['name'], c.user_data['id'], password=client['password'], ssl=client['ssl'])


def image_handler(u,c):
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    msg=u.message
    if msg.photo:
        file_id=msg.photo[-1].file_id
    else:
        logging.info("Wrong photo data")
        return

    newFile = c.bot.get_file(file_id)
    filename="/tmp/"+file_id
    newFile.download(filename)

    im = pyimgur.Imgur(CLIENT_ID)
    uploaded_image = im.upload_image(filename, title=u.message.text if hasattr(u.message, "text") else "Uploaded by https://t.me/ircclientbot")
    logging.info("Uploaded image")

    client = users[c.user_data['id']]
    send(c,u,uploaded_image.link)
    client.send(uploaded_image.link)
