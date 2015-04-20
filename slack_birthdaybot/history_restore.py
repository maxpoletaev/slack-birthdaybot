from datetime import datetime
from slacker import Slacker
import settings
import shelve


db = shelve.open(settings.DATABASE)
slack = Slacker(settings.API_KEY)

for im in slack.im.list().body["ims"]:
    channel_id = im["id"]
    user_id = im["user"]

    if user_id in db and "birthday" in db[user_id]:
        print("User %s already have a birthday.")
        continue

    print("Loading history for %s" % user_id)
    history = slack.im.history(channel_id).body["messages"]

    for msg in history:
        try:
            date = datetime.strptime(msg["text"], "%d.%m.%Y").date()
            print("Found %s for %s." % (date, user_id))
            db[user_id] = {"birthday": date}
            break
        except ValueError:
            pass

db.close()
