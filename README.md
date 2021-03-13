# IRCCLIENTBOT
This is an experimental attempt to create a basic irc client that works as
a telegram bot. It works as a bridge between telegram and any irc
server/channel. The limitations are that you can be logged to one
server/channel, ssl is not supported (yet) and only the most basic irc commands
are available.

## Demo
If you want you can try out the demo at: (https://t.me/ircclientbot)[https://t.me/ircclientbot]

## Create your own
You can also setup your own by getting an api token from botfather: (https://t.me/botfather)[https://t.me/botfather]
Then create a file env.py with the line:

`API_KEY="XXXXXX123123123"`

And run `python3 main.py`

