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


class SlackRtm:
    websocket = None
    conneced = False
    bindings = {}

    def __init__(self, client, debug=False):
        self.client = client
        self.debug = debug

    def connect(self):
        self.conneced = True
        response = self.client.rtm.start()
        self.websocket = create_connection(response.body['url'])

    def send(**kwargs):
        try:
            data = json.dumps(kwargs)
            self.websocket.send(data)
        except:
            self.connect()

    def read(self):
        return json.loads(self.websocket.recv())

    def ping(self):
        self.send(type="ping")

    def bind(self, event_type):
        def wrapper(func):
            if event_type not in self.bindings:
                self.bindings[event_type] = []
            self.bindings[event_type].append(func)
        return wrapper

    def forever(self):
        while self.conneced:
            event = RtmEvent(self.read())

            if self.debug:
                print(event.raw)

            if event.type in self.bindings and event.subtype != "bot_message":
                for func in self.bindings[event.type]:
                    func(event)

            time.sleep(1)

    def disconnect(self):
        self.conneced = False
        self.websocket.close()
