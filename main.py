import time
from automation.energenie import EnergenieClient
from automation.message_handler import MessageHandler

def main():
	APP_DELAY = 2
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

if __name__ == '__main__':
	main()
