# Birthday notifier for Slack

Put `API_KEY` into settings and run:

```
$ python slack_birthdaybot/receiver.py
```

Then set `NOTIFIER_CHANNEL` name in settings and add this to cron:

```
0 12 * * * python slack_birthdaybot/notifier.py
```
