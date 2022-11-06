import time
import json
from collections import namedtuple
from functools import partial
from paho.mqtt import client
from automation.energenie import EnergenieClient, EnergenieUpdateHandler, EnergenieUpdateReporter
from automation.swtich_handler import SwitchHandler
from automation.mqtt_handler import MQTTHandler


APP_DELAY = 2


Config = namedtuple("Config", "host, port, topic, listen_topic")


def switch_adapter(switch, switch_on: bool):
	if switch_on:
		switch.turn_on()
	else:
		switch.turn_off()


def setup_energenie_client(switch, host, topic):
	handler = EnergenieUpdateHandler()
	handler.power_status(switch)
	handler.reporter(EnergenieUpdateReporter(topic=topic, host=host))
	return EnergenieClient(handler=handler)


def setup_mqttHandler(callback, host, port, listen_topic):
	mqtt_handler = MQTTHandler(client_factory=client.Client)
	mqtt_handler.connect(host=host, port=port, keepalive=60)
	mqtt_handler.subscribe(listen_topic, callback=callback)
	return mqtt_handler


def load_config():
	with open('home_automation.conf') as f:
		conf = json.load(f)
		host = conf['HOST_ADDR']
		port = conf['HOST_PORT']
		topic = conf['SWITCH_PUBLISH_TOPIC']
		listen_topic = conf['SWITCH_LISTEN_TOPIC']

	return Config(host, port, topic, listen_topic)


def setup():
	config = load_config()
	print(f"config {config}")
	switch = SwitchHandler(switch_callback=None)
	energenie_client = setup_energenie_client(switch, host=config.host, topic=config.topic)

	switch.switch_callback = partial(switch_adapter, energenie_client.switch)

	mqtt_handler = setup_mqttHandler(callback=switch.flick_switch, host=config.host, port=config.port, listen_topic=config.listen_topic)

	return 	energenie_client, mqtt_handler


def main():
	energenie_client, mqtt_handler = setup()

	try:
		while True:
			energenie_client.loop()
			mqtt_handler.loop()
			time.sleep(APP_DELAY)
	finally:
		energenie_client.finished()


if __name__ == '__main__':  # pragma: no cover
	main()