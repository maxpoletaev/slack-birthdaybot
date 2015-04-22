from datetime import date, datetime, timedelta
from slacker import Slacker
import settings
import shelve


slack = Slacker(settings.API_KEY)
delta = timedelta(days=7)
today = date.today()

with shelve.open(settings.DATABASE) as db:
    for user_id, user_data in db.items():
        if "birthday" in user_data:
            birthday = user_data["birthday"].replace(year=today.year)

            if birthday - delta == today:
                info = slack.users.info(user_id).body
                message = "Господа, через неделю %s отмечает День Рождения." % info["user"]["real_name"]
                slack.chat.post_message("#" + settings.NOTIFIER_CHANNEL, message, username=settings.USERNAME)
