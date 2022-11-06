import json


class MQTTSwitchInfoPublisher:
    def __init__(self, topic, host, publisher):
        self.publisher = publisher
        self.mqtt_host = host
        self.switch_subject = topic

    def publish(self, data):
        try:
            self.publisher(topic=self.switch_subject, payload=json.dumps(data), hostname=self.mqtt_host)
        except Exception as err:
            print(f"Error publish: '{err}' data: {data}")
