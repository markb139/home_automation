import time
from paho.mqtt.publish import single
from paho.mqtt.client import Client
from automation.energenie import EnergenieClient
from automation.message_handler import MessageHandler
import json

def on_message(mqttc, obj, msg):
	print(f"Message {msg.payload}")

def on_subscribe(mqttc, obj, mid, granted_qos):
	print("Subscribed: " + str(mid) + " " + str(granted_qos))

def main():
	mqttc = Client()
	mqttc.on_subscribe = on_subscribe
	mqttc.on_message = on_message
	mqttc.connect("127.0.0.1", 1883, 60)
	mqttc.subscribe("switch/#", 0)
	while True:
		mqttc.loop()

if __name__ == '__main__':
	APP_DELAY    = 2
	m = MessageHandler()
	e = EnergenieClient(handler=m)
	m.set_switch(e.switch)
	
	try:
		while True:
			e.loop()
			m.loop()
			time.sleep(APP_DELAY)
	finally:
		e.finished()

#	main()
