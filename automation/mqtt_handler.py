import json
from paho.mqtt import client


class EmptyTopicException(Exception):
    pass

class MQTTHandler:
    def __init__(self, client_factory=None):
        self.client = client_factory()
        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect
        self.topic = None
        self.callback = None

    def _on_connect(self, client, userdata, flags, reason_code):
        print(f"on_connect userdata={userdata} flags={flags} reason_code={reason_code}")
        if self.topic:
            print(f"Subscribing to {self.topic}")
            self.client.subscribe(self.topic, 0)

    def connect(self, host, port, keepalive):
        res = self.client.connect(host=host, port=port, keepalive=keepalive)
        if res != client.MQTT_ERR_SUCCESS:
            raise Exception(f"Cannot connect {res}")

    def subscribe(self, topic: str, callback) -> bool:
        if topic:
            self.callback = callback
            self.topic = topic
            # self.client.subscribe(topic, 0)
        else:
            raise EmptyTopicException("Empty topic error")

    def _on_message(self, client, userdata, message):
        # print(f"MQTTHandler:_on_message {userdata} {message.payload}")
        payload = json.loads(message.payload)
        if isinstance(payload, bool):
            self.callback(payload)

    def loop(self):
        self.client.loop()
