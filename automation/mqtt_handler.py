import json
from paho.mqtt import client


class EmptyTopicException(Exception):
    pass

class MQTTHandler:
    def __init__(self, client_factory=None):
        self.client = client_factory()
        self.client.on_message = self._on_message
        self.callback = None

    def connect(self, host, port, keepalive):
        res = self.client.connect(host=host, port=port, keepalive=keepalive)
        if res != client.MQTT_ERR_SUCCESS:
            raise Exception(f"Cannot connect {res}")

    def subscribe(self, topic: str, callback) -> bool:
        if topic:
            self.callback = callback
            self.client.subscribe(topic, 0)
        else:
            raise EmptyTopicException("Empty topic error")

    def _on_message(self, client, userdata, message):
        # print(f"MQTTHandler:_on_message {userdata} {message.payload}")
        payload = json.loads(message.payload)
        if isinstance(payload, bool):
            self.callback(payload)

    def loop(self):
        self.client.loop()