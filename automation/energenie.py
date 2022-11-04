import datetime
from pyenergenie import energenie
from paho.mqtt.publish import single
from automation.message_handler import MQTTSwitchInfoPublisher

class EnergenieUpdateReporter:
	def __init__(self, topic, host):
		self.publisher = MQTTSwitchInfoPublisher(topic, host, publisher=single)

	def report(self, latest):
		self.publisher.publish(latest)


class EnergenieUpdateHandler:
	def __init__(self):
		self._power_status = None
		self._reporter = None

	def power_status(self, power_status):
		self._power_status = power_status

	def reporter(self, reporter):
		self._reporter = reporter

	def handle(self, data):
		print(f"Handler:handle {data}")
		self._power_status.switch_status(data['switch'])
		self._reporter.report(data)


class EnergenieClient:
	def __init__(self, handler=None):
		print("EnergenieClient")
		self._handler = handler
		energenie.init()
		energenie.registry.load_into(self)
		print(f'EnergenieClient.switch {self.switch}')
		self.switch.when_updated(self._update)

	def _update(self, d, payload):
		r = d.get_readings()
		self._latest = {
			'time': datetime.datetime.fromtimestamp(payload["rxtimestamp"]).isoformat(),
			'switch': r.switch,
			'voltage': r.voltage,
			'frequency': r.frequency,
			'current': r.current,
			'apparent_power': r.apparent_power,
			'reactive_power': r.reactive_power,
			'real_power': r.real_power,
			'powered': True if r.switch else False,
			'in_use':  True if r.real_power > 0 else False
		}
		if self._handler:
			self._handler.handle(self._latest)

	@staticmethod
	def loop():
		energenie.loop()
		
	@staticmethod
	def finished():
		energenie.finished()
