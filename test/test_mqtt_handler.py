from unittest import TestCase, mock
from paho.mqtt import client
from paho.mqtt.publish import single

from automation import mqtt_handler

class TestMQTTHandler(TestCase):

    def test_create(self):
        mock_client = mock.Mock(spec_set=client.Client)
        h = mqtt_handler.MQTTHandler(client_factory=mock_client)
        self.assertIsNotNone(h)
        mock_client.assert_called_once_with()

    def test_can_connect(self):
        mqtt_connect = mock.Mock(return_value=client.MQTT_ERR_SUCCESS)
        mock_client = mock.Mock(connect=mqtt_connect)
        mock_client_factory = mock.Mock(return_value=mock_client)
        h = mqtt_handler.MQTTHandler(client_factory=mock_client_factory)
        h.connect(host='localhost', port=1234, keepalive=60)
        mqtt_connect.assert_called_once_with(host='localhost', port=1234, keepalive=60)

    def test_raises_on_failed_connection(self):
        mqtt_connect = mock.Mock(return_value=client.MQTT_ERR_CONN_REFUSED)
        mock_client = mock.Mock(connect=mqtt_connect)
        mock_client_factory = mock.Mock(return_value=mock_client)
        h = mqtt_handler.MQTTHandler(client_factory=mock_client_factory)
        with self.assertRaises(Exception):
            h.connect(host='localhost', port=1234, keepalive=60)

    def test_can_subscribe(self):
        mqtt_subscribe = mock.Mock(return_value=(client.MQTT_ERR_SUCCESS, 0))
        mock_client = mock.Mock(subscribe=mqtt_subscribe)
        mock_client_factory = mock.Mock(return_value=mock_client)
        h = mqtt_handler.MQTTHandler(client_factory=mock_client_factory)
        h.subscribe(topic="switch/power_on", callback=mock.Mock())
        mqtt_subscribe.assert_called_once_with("switch/power_on", 0)

    def test_cannot_subscribe_with_empty_topic(self):
        mock_client_factory = mock.Mock()
        h = mqtt_handler.MQTTHandler(client_factory=mock_client_factory)
        callabck = mock.Mock()
        with self.assertRaises(Exception):
            h.subscribe(topic="", callback=callabck)

    def test_can_process_true_message(self):
        mqtt_subscribe = mock.Mock(return_value=(client.MQTT_ERR_SUCCESS, 0))
        mock_client = mock.Mock(subscribe=mqtt_subscribe)
        mock_client_factory = mock.Mock(return_value=mock_client)
        h = mqtt_handler.MQTTHandler(client_factory=mock_client_factory)
        callback = mock.Mock()
        h.subscribe(topic="switch/power_on", callback=callback)
        mock_client.on_message(client=1, userdata={}, message=mock.Mock(payload=b'true'))
        callback.assert_called_once_with(True)

    def test_can_process_false_message(self):
        mqtt_subscribe = mock.Mock(return_value=(client.MQTT_ERR_SUCCESS, 0))
        mock_client = mock.Mock(subscribe=mqtt_subscribe)
        mock_client_factory = mock.Mock(return_value=mock_client)
        h = mqtt_handler.MQTTHandler(client_factory=mock_client_factory)
        callback = mock.Mock()
        h.subscribe(topic="switch/power_on", callback=callback)
        mock_client.on_message(client=1, userdata={}, message=mock.Mock(payload=b'false'))
        callback.assert_called_once_with(False)

    def test_ignores_non_bool_message(self):
        mqtt_subscribe = mock.Mock(return_value=(client.MQTT_ERR_SUCCESS, 0))
        mock_client = mock.Mock(subscribe=mqtt_subscribe)
        mock_client_factory = mock.Mock(return_value=mock_client)
        h = mqtt_handler.MQTTHandler(client_factory=mock_client_factory)
        callback = mock.Mock()
        h.subscribe(topic="switch/power_on", callback=callback)
        mock_client.on_message(client=1, userdata={}, message=mock.Mock(payload=b'1234'))
        callback.assert_not_called()
