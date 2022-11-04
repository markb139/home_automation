from functools import partial
import datetime
from unittest import TestCase
from unittest import mock

from paho.mqtt import client

class ExitException(Exception):
    pass

class TestIntegration(TestCase):
    def test_one(self):
        updated_handler = None

        def _when_updated(_updater):
            nonlocal updated_handler
            updated_handler = _updater

        def _load(obj):
            obj.switch = mock.Mock(when_updated=mock.Mock(side_effect=_when_updated))

        def _loop():
            if updated_handler:
                updated_handler(mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(switch=False,
                                                                                        voltage=240,
                                                                                        frequency=50,
                                                                                        current=100,
                                                                                        apparent_power=100,
                                                                                        reactive_power=100,
                                                                                        real_power=100))),
                                {
                                    'rxtimestamp': datetime.datetime.now().timestamp()
                                })

        def _publish(topic, payload, hostname):
            print(f"Publish {topic}  {payload} {hostname}")

        def mqtt_loop():
            pass

        mock_client_obj = mock.Mock(connect=mock.Mock(return_value=client.MQTT_ERR_SUCCESS),
                                    subscribe=mock.Mock(return_value=(client.MQTT_ERR_SUCCESS, 1)),
                                    loop=mock.Mock(side_effect=mqtt_loop))

        mock_client = mock.Mock(Client=mock.Mock(return_value=mock_client_obj), MQTT_ERR_SUCCESS=client.MQTT_ERR_SUCCESS)

        mock_energenie = mock.Mock(registry=mock.Mock(load_into=mock.Mock(side_effect=_load)),
                                   loop=mock.Mock(side_effect=_loop))

        with mock.patch.dict('sys.modules', {
            'pyenergenie': mock.Mock(energenie=mock_energenie),
            'paho.mqtt': mock.Mock(client=mock_client),
            'paho.mqtt.publish': mock.Mock(single=mock.Mock(side_effect=_publish)),
            'time': mock.Mock(sleep=mock.Mock(side_effect=ExitException))
        }):
            from main import main
            with self.assertRaises(ExitException):
                main()

calls = [
    mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(switch=False,
                                                            voltage=240,
                                                            frequency=1,
                                                            current=100,
                                                            apparent_power=100,
                                                            reactive_power=100,
                                                            real_power=100))),
    mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(switch=True,
                                                            voltage=240,
                                                            frequency=2,
                                                            current=100,
                                                            apparent_power=100,
                                                            reactive_power=100,
                                                            real_power=100))),
    mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(switch=True,
                                                            voltage=240,
                                                            frequency=3,
                                                            current=100,
                                                            apparent_power=100,
                                                            reactive_power=100,
                                                            real_power=100))),
    mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(switch=False,
                                                            voltage=240,
                                                            frequency=4,
                                                            current=100,
                                                            apparent_power=100,
                                                            reactive_power=100,
                                                            real_power=100))),
    mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(switch=True,
                                                            voltage=240,
                                                            frequency=5,
                                                            current=100,
                                                            apparent_power=100,
                                                            reactive_power=100,
                                                            real_power=100))),
    mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(switch=True,
                                                            voltage=240,
                                                            frequency=6,
                                                            current=100,
                                                            apparent_power=100,
                                                            reactive_power=100,
                                                            real_power=100)))
]

mqtt_calls = [
    b'true',
    b'false',
    b'true',
    b'true',
    b'true',
    b'true',
    b'true',
]

class TestIntegrationNew(TestCase):
    def test_one(self):
        updated_handler = None
        mock_client_obj = None

        def _when_updated(_updater):
            nonlocal updated_handler
            updated_handler = _updater

        def _on():
            print("ON!")

        def _off():
            print("OFF!")

        def _load(obj):
            obj.switch = mock.Mock(when_updated=mock.Mock(side_effect=_when_updated),
                                   turn_on=mock.Mock(side_effect=_on),
                                   turn_off=mock.Mock(side_effect=_off))

        def _energenie_loop():
            if updated_handler and calls:
                updated_handler(calls.pop(0), {'rxtimestamp': datetime.datetime.now().timestamp() })

        mock_energenie = mock.Mock(registry=mock.Mock(load_into=mock.Mock(side_effect=_load)),
                                   loop=mock.Mock(side_effect=_energenie_loop))
        def mqtt_loop():
            nonlocal mock_client_obj
            if mqtt_calls:
                class _Msg:
                    payload = mqtt_calls.pop(0)
                message = _Msg()
                f = mock_client_obj.on_message
                f({}, {}, message)

        mock_client_obj = mock.Mock(connect=mock.Mock(return_value=client.MQTT_ERR_SUCCESS),
                                    subscribe=mock.Mock(return_value=(client.MQTT_ERR_SUCCESS, 1)),
                                    loop=mock.Mock(side_effect=mqtt_loop))

        mock_client = mock.Mock(Client=mock.Mock(return_value=mock_client_obj), MQTT_ERR_SUCCESS=client.MQTT_ERR_SUCCESS)

        def _time(delay):
            if len(calls) == 0 and len(mqtt_calls) == 0:
                raise ExitException()

        def _publish(topic, payload, hostname):
            print(f"Publish {topic}  {payload} {hostname}")
            if len(calls) == 1:
                raise Exception("BLASH")

        with mock.patch.dict('sys.modules', {
            'pyenergenie': mock.Mock(energenie=mock_energenie),
            'paho.mqtt': mock.Mock(client=mock_client),
            'paho.mqtt.publish': mock.Mock(single=mock.Mock(side_effect=_publish)),
            'time': mock.Mock(sleep=mock.Mock(side_effect=_time))
        }):
            from main import main_new
            with self.assertRaises(ExitException):
                main_new()
