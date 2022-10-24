from unittest import TestCase, mock
from paho.mqtt import client
from paho.mqtt.publish import single

from automation import message_handler
import automation

class TestMessageHandler(TestCase):
    def setUp(self) -> None:
        self.mock_client = mock.Mock(spec_set=client.Client())
        self.mock_client.connect.return_value = client.MQTT_ERR_SUCCESS
        self.mock_client.subscribe.return_value = (client.MQTT_ERR_SUCCESS, 0)

    def test_create(self):
        m = message_handler.MessageHandler(mqtt_client=self.mock_client)
        m.loop()
        self.assertIsNotNone(m)

    def test_handler_connects(self):
        message_handler.MessageHandler(mqtt_client=self.mock_client)
        self.mock_client.connect.assert_called_once_with('127.0.0.1', 1883, 60)

    def test_handler_connects_with_failure(self):
        self.mock_client.connect.return_value = client.MQTT_ERR_CONN_REFUSED
        with self.assertRaises(Exception):
            message_handler.MessageHandler(mqtt_client=self.mock_client)

    def test_handler_subscribes_ok(self):
        message_handler.MessageHandler(mqtt_client=self.mock_client)
        self.mock_client.subscribe.assert_called_once_with('home_automation/switch1/power_on', 0)

    def test_handler_subscribes_failure(self):
        self.mock_client.subscribe.return_value = (client.MQTT_ERR_NO_CONN, None)
        with self.assertRaises(Exception):
            message_handler.MessageHandler(mqtt_client=self.mock_client)

    def test_handler_handles(self):
        publisher_mock = mock.Mock(spec_set=single)
        m = message_handler.MessageHandler(mqtt_client=self.mock_client, publisher=publisher_mock)
        m.handle(latest={})
        publisher_mock.assert_called_once_with(topic='home_automation/switch1', payload='{}', hostname='127.0.0.1')

    def test_handler_handles_error(self):
        publisher_mock = mock.Mock(spec_set=single)
        publisher_mock.side_effect = Exception
        m = message_handler.MessageHandler(mqtt_client=self.mock_client, publisher=publisher_mock)
        m.handle(latest={})
        publisher_mock.assert_called_once_with(topic='home_automation/switch1', payload='{}', hostname='127.0.0.1')

    def test_handler_on_message_on(self):
        switch = mock.Mock()
        m = message_handler.MessageHandler(mqtt_client=self.mock_client)
        m.set_switch(switch)
        message = mock.Mock(payload=b'true')
        m.on_message(mqttc=None, obj=None, msg=message)
        switch.turn_on.assert_called_once()

    def test_handler_on_message_off(self):
        switch = mock.Mock()
        m = message_handler.MessageHandler(mqtt_client=self.mock_client)
        m.set_switch(switch)
        message = mock.Mock(payload=b'false')
        m.on_message(mqttc=None, obj=None, msg=message)
        switch.turn_off.assert_called_once()

    def test_handler_on_unexpected_message(self):
        switch = mock.Mock()
        m = message_handler.MessageHandler(mqtt_client=self.mock_client)
        m.set_switch(switch)
        message = mock.Mock(payload=b'BASL')
        m.on_message(mqttc=None, obj=None, msg=message)
        switch.turn_on.assert_not_called()
        switch.turn_off.assert_not_called()

class TestMessageHandlerRetry(TestMessageHandler):
    def test_retry_on(self):
        publisher_mock = mock.Mock(spec_set=single)
        switch = mock.Mock()
        m = message_handler.MessageHandler(mqtt_client=self.mock_client, publisher=publisher_mock)
        m.set_switch(switch)
        message = mock.Mock(payload=b'true')
        m.on_message(mqttc=None, obj=None, msg=message)
        m.handle(latest={"switch": False})
        self.assertEqual(2, len(switch.turn_on.mock_calls))
        self.assertEqual(1, m.retry_count)
        m.handle(latest={"switch": False})
        self.assertEqual(3, len(switch.turn_on.mock_calls))
        self.assertEqual(2, m.retry_count)
        m.handle(latest={"switch": True})
        self.assertEqual(3, len(switch.turn_on.mock_calls))
        self.assertEqual(0, m.retry_count)

    def test_retry_off(self):
        publisher_mock = mock.Mock(spec_set=single)
        switch = mock.Mock()
        m = message_handler.MessageHandler(mqtt_client=self.mock_client, publisher=publisher_mock)
        m.set_switch(switch)
        message = mock.Mock(payload=b'false')
        m.on_message(mqttc=None, obj=None, msg=message)
        m.handle(latest={"switch": True})
        self.assertEqual(2, len(switch.turn_off.mock_calls))
        self.assertEqual(1, m.retry_count)
        m.handle(latest={"switch": True})
        self.assertEqual(3, len(switch.turn_off.mock_calls))
        self.assertEqual(2, m.retry_count)
        m.handle(latest={"switch": False})
        self.assertEqual(3, len(switch.turn_off.mock_calls))
        self.assertEqual(0, m.retry_count)
        m.handle(latest={"switch": False})
