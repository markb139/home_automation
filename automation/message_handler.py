import json
from paho.mqtt.client import Client
from paho.mqtt.publish import single


class MessageHandler:
    def __init__(self):
        self.mqttc = Client()
        self.mqttc.on_subscribe = self.on_subscribe
        self.mqttc.on_message = self.on_message
        self.mqttc.connect("127.0.0.1", 1883, 60)
        self.mqttc.subscribe("home_automation/switch1/power_on", 0)
        self.expected_value = None
        self.retry_count = 0

    def set_switch(self, _switch):
        self._switch = _switch

    def handle(self, latest):
        print(f'{latest} expected {self.expected_value} {self.retry_count}')

        try:
            single(topic='home_automation/switch1', payload=json.dumps(latest), hostname='127.0.0.1')
        except Exception as err:
            print(err)
            print(latest)

        if self.expected_value is not None:
            try:
                if latest["switch"] == False:
                    if self.expected_value == True:
                        print("Retry - ON")
                        self._switch.turn_on()
                        self.retry_count += 1
                    else:
                        self.expected_value = None
                        self.retry_count = 0
                elif latest["switch"] == True:
                    if self.expected_value == False:
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

    def on_message(self, mqttc, obj, msg):
        if msg.payload == b'true':
            print('ON')
            self._switch.turn_on()
            self.expected_value=True
            self.retry_count = 0
        else:
            print('OFF')
            self._switch.turn_off()
            self.expected_value=False
            self.retry_count = 0

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def loop(self):
        self.mqttc.loop()
