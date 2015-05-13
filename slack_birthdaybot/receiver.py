from slacker import Error as SlackError
from utils import date_from_birthday
from datetime import datetime, date
from slackrtm import SlackRtm
from slacker import Slacker
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
            slack.chat.post_message(event.channel, msg, username=settings.USERNAME)
        else:
            msg = ("Я еще не знаю твою дату рождения. "
                   "Чтобы её установить, напиши `!set 10.03.1990`")
            slack.chat.post_message(event.channel, msg, username=settings.USERNAME)


@rtm.command("reset")
def reset_birthday(event):
    if not event.channel.startswith("D"):
        return

    with shelve.open(settings.DATABASE, writeback=True) as db:
        if event.user in db and "birthday" in db[event.user]:
            del db[event.user]["birthday"]

    slack.chat.post_message(event.channel, "Потрачено!", username=settings.USERNAME)


@rtm.command("soon")
def soon_birthday(event):
    today = date.today()
    sorted_users = {}

    def sort_by_bday(x):
        if "birthday" not in x[1]:
            return today

        birthday = x[1]["birthday"]
        return birthday.replace(year=today.year if birthday.replace(year=today.year) >= today else today.year + 1)

    with shelve.open(settings.DATABASE) as db:
        sorted_users = sorted(db.items(), key=sort_by_bday)

    output = []
    current_index, limit = (0, 3)

    for user_id, user in sorted_users:
        if current_index == limit:
            break

        if "birthday" in user:
            info = slack.users.info(user_id).body
            output.append("{date} — {user_name}".format(
                date=date_from_birthday(user["birthday"]),
                user_name=info["user"]["real_name"]
            ))

            current_index += 1

    output = "\n".join(output)
    slack.chat.post_message(event.channel, output, username=settings.USERNAME)


@rtm.command("default")
def show_help(event):
    if not event.channel.startswith("D"):
        return

    commands = "\n".join([
        "`!soon` — Показать ближайшие Дни Рождения",
        "`!set 10.03.1990` — Установить ваш День Рождения",
        "`!get` — Показать ваш День Рождения",
        "`!reset` — Сбросить ваш День Рождения",
    ])

    slack.chat.post_message(event.channel, commands, username=settings.USERNAME)


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
