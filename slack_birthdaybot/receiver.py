from slacker import Error as SlackError
from slacker import Slacker
from datetime import datetime
from slackrtm import SlackRtm
import os, sys, time
import settings
import shelve
import atexit


db = shelve.open(settings.DATABASE)
slack = Slacker(settings.API_KEY)
rtm = SlackRtm(slack, debug=settings.DEBUG)


def send_hello(user_id):
    channel = slack.im.open(user_id).body["channel"]["id"]
    message = "Привет. Мне нужна дата твоего рождения в формате 01.12.1990."
    slack.chat.post_message(channel, message, username=settings.USERNAME)


@rtm.bind("hello")
def send_hello_on_init(event):
    for user in slack.users.list().body["members"]:
        deleted = user["deleted"]
        user_id = user["id"]

        if user_id not in db and not deleted:
            presence = slack.users.get_presence(user_id).body["presence"]
            if presence == "active":
                send_hello(user_id)
                db[user_id] = {}

    db.sync()


@rtm.bind("presence_change")
def send_hello_on_presence_change(event):
    if event.user not in db and event.presence == "active":
        send_hello(event.user)
        db[event.user] = {}
        db.sync()


@rtm.bind("message")
def save_user_date(event):
    if not event.channel.startswith("D"):
        """ Is not direct message. """
        return

    try:
        date = datetime.strptime(event.text, "%d.%m.%Y").date()
        if event.user not in db: db[event.user] = {}
        db[event.user]["birthday"] = date
        db.sync()
    except ValueError:
        msg = "Я понимаю только даты в формате 01.12.1990."
    else:
        msg = "Запомнил!"

    slack.chat.post_message(event.channel, msg, username=settings.USERNAME)


if __name__ == "__main__":
    print("Bot started")

    @atexit.register
    def before_exit():
        rtm.disconnect()
        db.close()

    try:
        rtm.forever()
    except KeyboardInterrupt:
        before_exit()
