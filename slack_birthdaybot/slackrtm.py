from websocket import create_connection
import json, time


class RtmEvent:
    raw = None
    type = None
    subtype = None

    def __init__(self, data):
        self.raw = data
        for key, val in data.items():
            setattr(self, key, val)

        if self.type == "message":
            self.prevent_command = False


class SlackRtm:
    websocket = None
    connected = False

    _bindings = {}
    _commands = {}

    def __init__(self, client, debug=False):
        self.client = client
        self.debug = debug

    def connect(self):
        self.connected = True
        response = self.client.rtm.start()
        self.websocket = create_connection(response.body["url"])

    def send(**kwargs):
        data = json.dumps(kwargs)

        try:
            self.websocket.send(data)
        except:
            self.connect()
            self.websocket.send(data)

    def read(self):
        try:
            data = self.websocket.recv()
        except:
            self.connect()
            data = self.websocket.recv()

        return json.loads(data)

    def ping(self):
        self.send(type="ping")

    def bind(self, event_type):
        def wrapper(func):
            if event_type not in self._bindings:
                self._bindings[event_type] = []
            self._bindings[event_type].append(func)
            return func
        return wrapper

    def unbind(self, event_type, func):
        if event_type in self._bindings:
            for index, handler in enumerate(self._bindings[event_type]):
                if handler == func: del self._bindings[index]

    def command(self, command):
        def wrapper(func):
            self._commands[command] = func
            return func
        return wrapper

    def handle_event(self, event):
        if event.type in self._bindings:
            for func in self._bindings[event.type]:
                func(event)

    def handle_command(self, event):
        if event.text.startswith('!'):
            args = event.text.split()
            command = args[0][1:]

            if command in self._commands:
                handler = self._commands[command]
                return handler(event, *args[1:])

        if "default" in self._commands:
            handler = self._commands["default"]
            return handler(event)

    def main_loop(self):
        self.connect()

        while self.connected:
            event = RtmEvent(self.read())

            if self.debug:
                print(event.raw)

            if event.subtype != "bot_message":
                self.handle_event(event)

                if event.type == "message" and not event.prevent_command:
                    self.handle_command(event)

            time.sleep(1)

    def disconnect(self):
        self.connected = False
        self.websocket.close()
