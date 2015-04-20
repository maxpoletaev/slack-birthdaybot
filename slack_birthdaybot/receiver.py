from slacker import Error as SlackError
from slacker import Slacker
from datetime import datetime
from slackrtm import SlackRtm
import os, sys, time
import settings
import shelve
import atexit


slack = Slacker(settings.API_KEY)
rtm = SlackRtm(slack, debug=settings.DEBUG)


def send_hello(user_id):
    channel = slack.im.open(user_id).body["channel"]["id"]
    message = "Привет. Мне нужна дата твоего рождения в формате 01.12.1990."
    slack.chat.post_message(channel, message, username=settings.USERNAME)


@rtm.bind("hello")
def send_hello_on_init(event):
    db = shelve.open(settings.DATABASE)
    for user in slack.users.list().body["members"]:
        deleted = user["deleted"]
        user_id = user["id"]

        if user_id not in db and not deleted:
            presence = slack.users.get_presence(user_id).body["presence"]
            if presence == "active":
                send_hello(user_id)
                db[user_id] = {}

    db.close()


@rtm.bind("presence_change")
def send_hello_on_presence_change(event):
    db = shelve.open(settings.DATABASE)
    if event.user not in db and event.presence == "active":
        send_hello(event.user)
        db[event.user] = {}

    db.close()


@rtm.bind("message")
def save_user_date(event):
    if not event.channel.startswith("D"):
        """ Is not direct message. """
        return

    try:
        text = event.text.strip()
        date = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        msg = "Я понимаю только даты в формате 01.12.1990."
        slack.chat.post_message(event.channel, msg, username=settings.USERNAME)
        return

    with shelve.open(settings.DATABASE) as db:
        db[event.user] = {"birthday": date}

    msg = "Запомнил!"
    slack.chat.post_message(event.channel, msg, username=settings.USERNAME)


if __name__ == "__main__":
    print("Bot started")

    @atexit.register
    def before_exit():
        rtm.disconnect()

    try:
        rtm.forever()
    except KeyboardInterrupt:
        before_exit()
