def date_from_birthday(birthday):
    months = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля",
              "августа", "сентября", "октября", "ноября", "декабря")
    return "%s %s" % (birthday.day, months[birthday.month - 1])
