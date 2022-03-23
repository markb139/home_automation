import sys
import datetime
from pyenergenie import energenie

class EnergenieClient:
	def __init__(self, handler=None):
		print("EnergenieClient")
		self._handler = handler
		energenie.init()
		#me_global = sys.modules[__name__]
		energenie.registry.load_into(self)
		print(f'switch {self.switch}')
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
            'powered': 'true' if r.switch else 'false',
			'in_use':  'true' if r.real_power > 0 else 'false'
            }
		if self._handler:
			self._handler.handle(self._latest)

	
	@staticmethod
	def loop():
		energenie.loop()
		
	@staticmethod
	def finished():
		energenie.finished()

