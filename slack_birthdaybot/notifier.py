from datetime import date, datetime, timedelta
from slacker import Slacker
import settings
import random
import shelve


slack = Slacker(settings.API_KEY)
week_delta = timedelta(days=7)
two_day_delta = timedelta(days=2)
today = date.today()


def random_smile():
    smiles = [":data:", ":gift:", ":birthday:", ":balloon:"]
    return random.choice(smiles)


def send_message(message, exclude=[]):
    for user in slack.users.list().body["members"]:
        user_id = user["id"]
        if not user["deleted"] and user_id not in exclude:
            channel = slack.im.open(user_id).body["channel"]["id"]
            slack.chat.post_message(channel, message, username=settings.USERNAME)


def date_from_birthday(birthday):
    months = ("января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря")
    return "%s %s" % (birthday.day, months[birthday.month - 1])


with shelve.open(settings.DATABASE) as db:
    for user_id, user_data in db.items():
        if "birthday" in user_data:
            birthday = user_data["birthday"].replace(year=today.year)

            if birthday - week_delta == today:
                info = slack.users.info(user_id).body
                human_date = date_from_birthday(birthday)

                message = "Псс… Через неделю, {date}, {name} отмечает День Рождения {smile}" \
                    .format(date=human_date, name=info["user"]["real_name"], smile=random_smile())

                send_message(message, exclude=[user_id])

            elif birthday - two_days_delta == today:
                info = slack.users.info(user_id).body
                message = "Псс… Послезавтра {name} отмечает День Рождения {smile}" \
                    .format(name=info["user"]["real_name"], smile=random_smile())

                send_message(message, exclude=[user_id])
