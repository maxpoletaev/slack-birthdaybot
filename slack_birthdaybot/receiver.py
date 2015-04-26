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


@rtm.command("set")
def set_birthday(event, date=None):
    if not event.channel.startswith("D"):
        return

    if not date:
        msg = "Я ожидал услышать что-то вроде `!set 01.12.1990`."
        slack.chat.post_message(event.channel, msg, username=settings.USERNAME)
        return

    if isinstance(date, str):
        try:
            date = datetime.strptime(date, "%d.%m.%Y").date()
        except ValueError:
            msg = "Я понимаю только даты в формате 01.12.1990."
            slack.chat.post_message(event.channel, msg, username=settings.USERNAME)
            return

    with shelve.open(settings.DATABASE) as db:
        db[event.user] = {"birthday": date}

    msg = "Запомнил!"
    slack.chat.post_message(event.channel, msg, username=settings.USERNAME)


@rtm.command("get")
def get_birthday(event):
    if not event.channel.startswith("D"):
        return

    with shelve.open(settings.DATABASE) as db:
        if event.user in db and "birthday" in db[event.user]:
            msg = "Твоя дата рождения: %s" % db[event.user]["birthday"]
            slack.chat.post_message(event.channel, msg)
        else:
            msg = ("Я еще не знаю твою дату рождения. "
                   "Чтобы её установить, напиши `!set 10.03.1990`")
            slack.chat.post_message(event.channel, msg)


@rtm.command("reset")
def reset_birthday(event):
    if not event.channel.startswith("D"):
        return

    with shelve.open(settings.DATABASE, writeback=True) as db:
        if event.user in db and "birthday" in db[event.user]:
            del db[event.user]["birthday"]

    slack.chat.post_message(event.channel, "Потрачено!")


@rtm.command("default")
def show_help(event):
    if not event.channel.startswith("D"):
        return

    commands = "\n".join([
        "`!set 10.03.1990` — Установить ваш День Рождения",
        "`!get` — Показать ваш День Рождения",
        "`!reset` — Сбросить ваш День Рождения",
    ])

    slack.chat.post_message(event.channel, commands)


@rtm.bind("message")
def set_birthday_from_message(event):
    if not event.channel.startswith("D"):
        return

    try:
        text = event.text.strip()
        date = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        return

    event.prevent_command = True
    set_birthday(event, date)


if __name__ == "__main__":
    print("Bot started")

    @atexit.register
    def before_exit():
        rtm.disconnect()

    try:
        rtm.main_loop()
    except KeyboardInterrupt:
        before_exit()
