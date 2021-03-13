import logging
from ircclient import ircJoin, ircDisconnect, send
from users import UsersList
users = UsersList()


def connect(u, c):
    args = u.message.text.split()[1:]
    if len(args) == 0:
        send(c, u, "Please specify a hostname and a port(defaults to 6667)")
        return
    ircJoin(u, c, str(args[0]), int(args[1]) if len(args) > 1 else 6667)


def join(u, c):
    args = u.message.text.split()[1:]
    if len(args) == 0:
        send(c, u, "Please, specify a channel to join")
        return
    channel = c.user_data['channel'] = args[0]
    client = users[c.user_data['id']]
    client.send_raw(f"PART {client.channel}")
    logging.info("JOINING-----------------------------------"+channel)
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
    send(c, u, str(c.user_data))


def bridge(u, c):
    global users
    logging.info("---------------------------------------")
    # or (c.user_data['id'] in users and not users[c.user_data['id']]['on']):
    if not c.user_data['id'] in users:
        send(c, u, "You are not connected to any irc")
        return
    try:
        client = users[c.user_data['id']]
        client.send(u.message.text)
    except:
        send(c, u, "You were disconnected! Connect again")
        try:
            del users[c.user_data['id']]
        except:
            pass


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
    if ('saved' in c.user_data and not name in c.user_data['saved']) or not 'saved' in c.user_data:
        if not 'saved' in c.user_data:
            c.user_data['saved'] = {}
        c.user_data['saved'][name] = {
            'host': client.host, 'name': client.name, 'port': client.port, 'channel': client.channel}
        send(c, u, f"Saved {name}!")
    else:
        send(c, u, "You already used that name, please choose another one")


def load(u, c):
    args = u.message.text.split()[1:]
    if len(args) == 0:
        send(c, u, "Please, specify a name to load from")
        return
    name = args[0]
    if not 'saved' in c.user_data:
        send(c, u, "You don't have anything saved yet")
        return
    try:
        ircDisconnect(c)
    except:
        pass
    client = c.user_data['saved'][name]
    send(c,u,str(client))
    ircJoin(u, c, client['host'], client['port'], client['channel'])


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
