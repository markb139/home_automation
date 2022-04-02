import json
import socket
import struct
import pytz
from collections import namedtuple
from datetime import date, datetime


Thermo = namedtuple('Thermo', 'set_temp current_temp heat_on time error_code')
HEADER = namedtuple('HEADER', ['frame_head', 'frame_length', 'start_address', 'number_of_bytes'])


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))



class Heatmiser:
	def __init__(self):
		with open('heatmiser.conf') as f:
			conf = json.load(f)
			print(conf)
			self.HOST_ADDR = (conf['HOST_ADDR'], conf['HOST_PORT'])
			self.pin_h = int(conf["PIN"][0:2],16)
			self.pin_l = int(conf["PIN"][2:4],16)
		self.SOCKET_TIMEOUT = 15.0
	
	@staticmethod
	def calc_crc(data):
		def crc16_4bits(crc, nibble):
			lookup = [
				0x0000, 0x1021, 0x2042, 0x3063,
				0x4084, 0x50A5, 0x60C6, 0x70E7,
				0x8108, 0x9129, 0xA14A, 0xB16B,
				0xC18C, 0xD1AD, 0xE1CE, 0xF1EF
			]
			return ((crc << 4) & 0xffff) ^ lookup[(crc >> 12) ^ nibble]

		crc = 0xffff;
		for d in data:
			crc = crc16_4bits(crc, d >> 4)
			crc = crc16_4bits(crc, d & 0x0f)

		return crc

	def create_read_request(self):
		packet = (0x93, 11, 0, 0xea, 0x21, 00, 00, 0xff, 0xff)
		packer = struct.Struct('B B B B B B B B B')
		packed_data = packer.pack(*packet)
		crc = Heatmiser.calc_crc(packed_data)
		packed_crc = struct.pack('H', crc)
		return packed_data + packed_crc

	@staticmethod
	def read_crc(s):
		raw_data = Heatmiser.read_bytes(2, s)
		crc = struct.unpack('<H', raw_data)[0]
		return crc

	@staticmethod
	def read_dcb(dcb_len, s):
		raw_data = Heatmiser.read_bytes(dcb_len, s)
		DCB = namedtuple('DCB',
						 ['dcb_len',
						  'vendor_id',
						  'conf',
						  'model',
						  'temp_format',
						  'switch_diff',
						  'frost_prot',
						  'calibration_off',
						  'out_delay',
						  'add_',
						  'key_limit',
						  'sensor_selection',
						  'opt_start',
						  'rate_of_change',
						  'program_mode',
						  'frost_protect',
						  'set_room_temp',
						  'floor_max',
						  'floor_max_limit',
						  'on_off',
						  'key_lock',
						  'run_mode',
						  'away_mode',
						  'hol_yr', 'hol_mn', 'hol_dy', 'hol_hr','hol_min', 'hol_en',
						  'temp_hold_minutes',
						  'remote_temp',
						  'floor_temp',
						  'air_temp',
						  'error_code',
						  'current_heating_state',
						  'year', 'month', 'day', 'week', 'hour', 'min', 'sec'])
		h = DCB._make(struct.unpack('<HBBBBBBHBBBBBBBBBBBBBBBBBBBBBHHHHBBBBBBBBB', raw_data[0:48]))
		return h, raw_data

	@staticmethod
	def read_bytes(length, s):
		return s.recv(length)

	@staticmethod
	def read_header(s):
		raw_data = Heatmiser.read_bytes(7, s)
		h = HEADER._make(struct.unpack('<BHHH', raw_data))
		if h.number_of_bytes > 0:
			return h.number_of_bytes, raw_data
		else:
			raise Exception("PIN Error")

	@staticmethod
	def process_response(s):
		dcb_len, raw_header = Heatmiser.read_header(s)
		data, raw_data = Heatmiser.read_dcb(dcb_len, s)
		crc = Heatmiser.read_crc(s)
		calculated_crc = Heatmiser.calc_crc(raw_header+raw_data)
		if calculated_crc == crc:
			return data
		else:
			raise Exception(f"CRC failure calculated crc 0x{calculated_crc:04x} sent crc 0x{crc:04x}")

	def perform_query(self, packet):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.settimeout(self.SOCKET_TIMEOUT)
			s.connect(self.HOST_ADDR)
			s.sendall(packet)
			return Heatmiser.process_response(s)

	def get_current_data(self):
		dcb_data = self.perform_query(self.create_read_request())

		return Thermo(set_temp=dcb_data.set_room_temp,
		              current_temp=dcb_data.air_temp,
					  heat_on=dcb_data.current_heating_state,
                      error_code=dcb_data.error_code,
                      time=datetime(year=2000 + dcb_data.year,
									month=dcb_data.month,
                                    day=dcb_data.day,
                                    hour=dcb_data.hour,
                                    minute=dcb_data.min,
                                    second=dcb_data.sec).astimezone(pytz.UTC))


if __name__ == '__main__':
	h = Heatmiser()
	reading = json.dumps(h.get_current_data()._asdict(), default=json_serial)
	print(f'Current reading {reading}')
