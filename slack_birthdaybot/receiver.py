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
rtm.connect()


@rtm.bind("message")
def save_user_date(event):
    if not event.channel.startswith("D"):
        """ Is not direct message. """
        return

    try:
        date = datetime.strptime(event.text, "%d.%m.%Y").date()
        db[event.user] = {"birthday": date}
        db.sync()
    except ValueError:
        msg = "Мне нужна дата твоего рождения в формате 01.12.1990."
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
