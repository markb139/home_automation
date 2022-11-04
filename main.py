import time
from functools import partial
from paho.mqtt import client
from automation.energenie import EnergenieClient, EnergenieUpdateHandler, EnergenieUpdateReporter
from automation.message_handler import MessageHandler, MQTTSwitchInfoPublisher
from automation.swtich_handler import SwitchHandler
from automation.mqtt_handler import MQTTHandler


APP_DELAY = 2
HOST = 'raspberrypi-2.local'
PORT = 1884
SWITCH_LISTEN_TOPIC = "home_automation/switch1/power_on"
SWITCH_PUBLISH_TOPIC = 'home_automation/switch1'


def switch_adapter(switch, switch_on: bool):
	if switch_on:
		switch.turn_on()
	else:
		switch.turn_off()


def setup_energenie_client(switch):
	handler = EnergenieUpdateHandler()
	handler.power_status(switch)
	handler.reporter(EnergenieUpdateReporter(topic=SWITCH_PUBLISH_TOPIC, host=HOST))
	return EnergenieClient(handler=handler)


def setup_mqttHandler(callback):
	mqtt_handler = MQTTHandler(client_factory=client.Client)
	mqtt_handler.connect(host=HOST, port=PORT, keepalive=60)
	mqtt_handler.subscribe(SWITCH_LISTEN_TOPIC, callback=callback)
	return mqtt_handler


def main_new():
	switch = SwitchHandler(switch_callback=None)
	energenie_client = setup_energenie_client(switch)

	switch.switch_callback = partial(switch_adapter, energenie_client.switch)

	mqtt_handler = setup_mqttHandler(callback=switch.flick_switch)

	try:
		while True:
			energenie_client.loop()
			mqtt_handler.loop()
			time.sleep(APP_DELAY)
	finally:
		energenie_client.finished()


def main():
	m = MessageHandler(mqtt_client=client.Client())
	e = EnergenieClient(handler=m)
	m.set_switch(e.switch)
	
	try:
		while True:
			e.loop()
			m.loop()
			time.sleep(APP_DELAY)
	finally:
		e.finished()


if __name__ == '__main__':
	# main()
	main_new()