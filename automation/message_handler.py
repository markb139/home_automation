import json
from paho.mqtt import client
from paho.mqtt.publish import single

class MQTTCommandAdapter:
    def __init__(self, parent, switch_subject, mqtt_client):
        self.parent = parent
        self.mqttc = mqtt_client
        self.mqtt_switch = switch_subject
        self.mqtt_host = '127.0.0.1'
        self.mqttc.on_subscribe = self.on_subscribe
        self.mqttc.on_message = self.on_message
        res = self.mqttc.connect(self.mqtt_host, 1883, 60)
        if res != client.MQTT_ERR_SUCCESS:
            raise Exception("Connection failed")

        result, mid = self.mqttc.subscribe(f"{self.mqtt_switch}/power_on", 0)
        if result != client.MQTT_ERR_SUCCESS:
            raise Exception("Subscribe failed")

    def on_message(self, mqttc, obj, msg):
        self.parent.on_message(mqttc, obj, msg)

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def loop(self):
        self.mqttc.loop()

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

class MessageHandler:
    def __init__(self, mqtt_client=None, publisher=single):
        self.switch_subject = 'home_automation/switch1'
        self.mqtt_host = '127.0.0.1'
        self._switch = None
        self.expected_value = None
        self.retry_count = 0

        self.adapter = MQTTCommandAdapter(self, self.switch_subject, mqtt_client)
        self.switch_publisher = MQTTSwitchInfoPublisher(self.switch_subject, self.mqtt_host, publisher)

    def set_switch(self, _switch):
        self._switch = _switch

    def handle(self, latest):
        print(f'{latest} expected {self.expected_value} retry {self.retry_count}')

        self.switch_publisher.publish(latest)

        if self.expected_value is not None:
            try:
                if not latest["switch"] :
                    if self.expected_value:
                        print("Retry - ON")
                        self._switch.turn_on()
                        self.retry_count += 1
                    else:
                        self.expected_value = None
                        self.retry_count = 0
                elif latest["switch"]:
                    if not self.expected_value:
                        print("Retry - OFF")
                        self._switch.turn_off()
                        self.retry_count += 1
                    else:
                        self.expected_value = None
                        self.retry_count = 0
                else:
                        print("Unexpected value of switch")
            except Exception as err:
                print(err)
                print(latest)
        else:
            pass
            #print("No need to retry")

    def on_message(self, mqttc, obj, msg):
        if msg.payload == b'true':
            print('ON')
            self._switch.turn_on()
            self.expected_value=True
            self.retry_count = 0
        elif msg.payload == b'false':
            print('OFF')
            self._switch.turn_off()
            self.expected_value=False
            self.retry_count = 0
        else:
            print(f"Unexpected message {msg.payload}")

    def loop(self):
        self.adapter.loop()
