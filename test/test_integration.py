from functools import partial
from collections import namedtuple
import datetime
from unittest import TestCase
from unittest import mock

from paho.mqtt import client


from automation.mqtt_handler import EmptyTopicException


class ExitException(Exception):
    pass


Reading = namedtuple("Reading","switch, voltage, frequency, current, apparent_power, reactive_power, real_power")
MQTTCall = namedtuple("MQTTCall", "payload")

class TestIntegrationNew(TestCase):
    def _time(self, delay):
        if len(self.calls) == 0 and len(self.mqtt_calls) == 0:
            raise ExitException()

    def _publish(self, topic, payload, hostname):
        self.published.append(payload)
        if len(self.calls) == 1 and self.publish_errors is not None:
            self.publish_errors.append('Some error publishing')
            raise Exception("Some error publishing")

    def mqtt_loop(self):
        if self.mqtt_calls:
            message = self.mqtt_calls.pop(0)
            # de-reference func object before calling. Mock tries to be clever
            (self.mock_client_obj.on_message)({}, {}, message)

    def _when_updated(self, _updater):
        self.updated_handler = _updater

    def _on(self):
        self.results.append('ON')

    def _off(self):
        self.results.append('OFF')

    def _load(self, obj):
        obj.switch = mock.Mock(when_updated=mock.Mock(side_effect=self._when_updated),
                               turn_on=mock.Mock(side_effect=self._on),
                               turn_off=mock.Mock(side_effect=self._off))

    def _energenie_loop(self):
        self.updated_handler(self.calls.pop(0), {'rxtimestamp': datetime.datetime.now().timestamp() })

    def setUp(self) -> None:
        self.published = []
        self.results = []
        self.publish_errors = None
        self.updated_handler = None

        self.mock_client_obj = mock.Mock(connect=mock.Mock(return_value=client.MQTT_ERR_SUCCESS),
                                    subscribe=mock.Mock(return_value=(client.MQTT_ERR_SUCCESS, 1)),
                                    loop=mock.Mock(side_effect=self.mqtt_loop))

        self.mock_client = mock.Mock(Client=mock.Mock(return_value=self.mock_client_obj), MQTT_ERR_SUCCESS=client.MQTT_ERR_SUCCESS)


        self.mock_energenie = mock.Mock(registry=mock.Mock(load_into=mock.Mock(side_effect=self._load)),
                                        loop=mock.Mock(side_effect=self._energenie_loop))

    def _patch_libs(self):
        return mock.patch.dict('sys.modules', {
            'pyenergenie': mock.Mock(energenie=self.mock_energenie),
            'paho.mqtt': mock.Mock(client=self.mock_client),
            'paho.mqtt.publish': mock.Mock(single=mock.Mock(side_effect=self._publish)),
            'time': mock.Mock(sleep=mock.Mock(side_effect=self._time))

        })

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": "home_automation/switch1/power_on"}"""))
    def test_connection_fails(self):
        self.mock_client_obj.connect.return_value=client.MQTT_ERR_CONN_REFUSED
        with self._patch_libs():
            from main import main
            with self.assertRaises(Exception):
                main()

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": ""}"""))
    def test_no_listen_topic(self):
        self.calls = [mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(**r._asdict())))
                      for r in [
                          Reading(False, 240, 1, 100, 100, 100, 100),
                          Reading(True, 240, 2, 100, 100, 100, 100),
                      ]]

        self.mqtt_calls = [MQTTCall(b'true')]

        with self._patch_libs():
            from main import main
            with self.assertRaises(EmptyTopicException):
                    main()

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": "home_automation/switch1/power_on"}"""))
    def test_switch_on(self):
        self.calls = [mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(**r._asdict())))
                      for r in [
                          Reading(False, 240, 1, 100, 100, 100, 100),
                          Reading(True, 240, 2, 100, 100, 100, 100),
                      ]]

        self.mqtt_calls = [MQTTCall(b'true')]

        with self._patch_libs():
            from main import main
            with self.assertRaises(ExitException):
                main()

        # we should check the expected results
        self.assertEqual(['ON'], self.results)

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": "home_automation/switch1/power_on"}"""))
    def test_switch_off(self):
        self.calls = [mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(**r._asdict())))
                      for r in [
                          Reading(False, 240, 1, 100, 100, 100, 100),
                          Reading(False, 240, 2, 100, 100, 100, 100),
                          Reading(False, 240, 2, 100, 100, 100, 100)
                      ]]

        self.mqtt_calls = [MQTTCall(b'false')]

        with self._patch_libs():
            from main import main
            with self.assertRaises(ExitException):
                main()

        # we should check the expected results
        self.assertEqual(['OFF'], self.results)

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": "home_automation/switch1/power_on"}"""))
    def test_publish_error_handler(self):
        self.publish_errors = []
        self.calls = [mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(**r._asdict())))
                      for r in [
                          Reading(False, 240, 1, 100, 100, 100, 100),
                          Reading(True, 240, 2, 100, 100, 100, 100),
                      ]]

        self.mqtt_calls = [
            MQTTCall(b'true'),
            MQTTCall(b'false'),
        ]

        with self._patch_libs():
            from main import main
            with self.assertRaises(ExitException):
                main()

        # we should check the expected results
        self.assertEqual(['ON', 'OFF'], self.results)
        self.assertEqual(['Some error publishing'], self.publish_errors)
        self.assertEqual(2, len(self.published))

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": "home_automation/switch1/power_on"}"""))
    def test_5_on_retries(self):
        self.calls = [mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(**r._asdict())))
                      for r in [
                          Reading(False, 240, 1, 100, 100, 100, 100),
                          Reading(False, 240, 2, 100, 100, 100, 100),
                          Reading(False, 240, 3, 100, 100, 100, 100),
                          Reading(False, 240, 4, 100, 100, 100, 100),
                          Reading(False, 240, 5, 100, 100, 100, 100),
                      ]]

        self.mqtt_calls = [
            MQTTCall(b'true'),
        ]

        with self._patch_libs():
            from main import main
            with self.assertRaises(ExitException):
                main()

        # we should check the expected results
        self.assertEqual(['ON', 'ON', 'ON', 'ON', 'ON'], self.results)
        self.assertEqual(5, len(self.published))

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": "home_automation/switch1/power_on"}"""))
    def test_5_off_retries(self):
        self.calls = [mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(**r._asdict())))
                      for r in [
                          Reading(False, 240, 1, 100, 100, 100, 100),
                          Reading(True, 240, 2, 100, 100, 100, 100),
                          Reading(True, 240, 3, 100, 100, 100, 100),
                          Reading(True, 240, 4, 100, 100, 100, 100),
                          Reading(True, 240, 5, 100, 100, 100, 100),
                      ]]

        self.mqtt_calls = [
            MQTTCall(b'false'),
        ]

        with self._patch_libs():
            from main import main
            with self.assertRaises(ExitException):
                main()

        # we should check the expected results
        self.assertEqual(['OFF', 'OFF', 'OFF', 'OFF', 'OFF'], self.results)
        self.assertEqual(5, len(self.published))

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": "home_automation/switch1/power_on"}"""))
    def test_several_ons(self):
        self.calls = [mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(**r._asdict())))
                      for r in [
                          Reading(False, 240, 1, 100, 100, 100, 100),
                          Reading(True, 240, 2, 100, 100, 100, 100),
                          Reading(True, 240, 3, 100, 100, 100, 100),
                          Reading(False, 240, 4, 100, 100, 100, 100),
                          Reading(True, 240, 5, 100, 100, 100, 100),
                          Reading(True, 240, 6, 100, 100, 100, 100),
                          Reading(True, 240, 7, 100, 100, 100, 100),
                          Reading(True, 240, 8, 100, 100, 100, 100),
                      ]]

        self.mqtt_calls = [
            MQTTCall(b'true'),
            MQTTCall(b'false'),
            MQTTCall(b'true'),
            MQTTCall(b'true'),
            MQTTCall(b'true'),
            MQTTCall(b'true'),
            MQTTCall(b'true'),
        ]

        with self._patch_libs():
            from main import main
            with self.assertRaises(ExitException):
                main()

        # we should check the expected results
        self.assertEqual(['ON', 'OFF', 'OFF', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON'], self.results)
        self.assertEqual(8, len(self.published))

    @mock.patch("builtins.open", mock.mock_open(read_data="""{"HOST_ADDR": "raspberrypi-2.local","HOST_PORT": 1884,"SWITCH_PUBLISH_TOPIC":"home_automation/switch1", "SWITCH_LISTEN_TOPIC": "home_automation/switch1/power_on"}"""))
    def test_unexpected_message(self):
        self.calls = [mock.Mock(get_readings=mock.Mock(return_value=mock.Mock(**r._asdict())))
                      for r in [
                          Reading(False, 240, 1, 100, 100, 100, 100),
                          Reading(False, 240, 2, 100, 100, 100, 100),
                      ]]

        self.mqtt_calls = [
            MQTTCall(b'"a string"'),
            MQTTCall(b'1234'),
        ]

        with self._patch_libs():
            from main import main
            with self.assertRaises(ExitException):
                main()

        # we should check the expected results
        self.assertEqual([], self.results)
        self.assertEqual(2, len(self.published))
