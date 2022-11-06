from unittest import TestCase, mock

from automation import swtich_handler

class TestSwitchHandler(TestCase):
    def setUp(self):
        pass

    def test_can_create(self):
        handler = swtich_handler.SwitchHandler()
        self.assertIsNotNone(handler)

    def test_can_set_callback(self):
        handler = swtich_handler.SwitchHandler()
        obj = object
        handler.switch_callback = obj
        self.assertEqual(obj, handler.switch_callback)

    def test_report_status_on(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.switch_status = True
        self.assertTrue(handler.switch_status)
        callback.assert_not_called()

    def test_report_status_off(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.switch_status = False
        self.assertFalse(handler.switch_status)
        callback.assert_not_called()

    def test_can_switch_on(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.flick_switch(True)
        self.assertTrue(handler.is_trying)
        callback.assert_called_once_with(switch_on=True)

    def test_can_switch_off(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.flick_switch(False)
        self.assertTrue(handler.is_trying)
        callback.assert_called_once_with(switch_on=False)

    def test_can_switch_on_callsout(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.flick_switch(True)
        self.assertTrue(handler.is_trying)
        callback.assert_called_once_with(switch_on=True)

    def test_can_switch_off_callsout(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.flick_switch(False)
        self.assertTrue(handler.is_trying)
        callback.assert_called_once_with(switch_on=False)

    def test_can_switch_on_callsout_and_retries(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.flick_switch(True)
        self.assertTrue(handler.is_trying)
        handler.switch_status(False)
        self.assertTrue(handler.is_trying)
        handler.switch_status(True)
        self.assertFalse(handler.is_trying)

        callback.assert_has_calls([mock.call(switch_on=True), mock.call(switch_on=True)])

    def test_can_switch_off_callsout_and_retries(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.flick_switch(False)
        self.assertTrue(handler.is_trying)
        handler.switch_status(True)
        self.assertTrue(handler.is_trying)
        handler.switch_status(False)
        self.assertFalse(handler.is_trying)
        handler.switch_status(False)
        handler.switch_status(False)
        callback.assert_has_calls([mock.call(switch_on=False), mock.call(switch_on=False)])

    def test_can_switch_off_callsout_and_stops_retries(self):
        callback = mock.Mock()
        handler = swtich_handler.SwitchHandler(switch_callback=callback)
        handler.flick_switch(False)
        self.assertTrue(handler.is_trying)
        handler.switch_status(True)
        self.assertTrue(handler.is_trying)
        handler.switch_status(False)
        self.assertFalse(handler.is_trying)
        handler.switch_status(False)
        handler.switch_status(True)
        self.assertFalse(handler.is_trying)
        callback.assert_has_calls([mock.call(switch_on=False), mock.call(switch_on=False)])
