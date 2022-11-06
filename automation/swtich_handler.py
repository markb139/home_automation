class SwitchHandler:
    def __init__(self, switch_callback):
        self._switch_status = None
        self._expected = None
        self._switch_callback = switch_callback

    @property
    def is_trying(self): # pragma: no cover
        return self._expected is not None

    @property
    def switch_callback(self):
        return self._switch_callback

    @switch_callback.setter
    def switch_callback(self, callback):
        self._switch_callback = callback

    # @switch_status.setter
    def switch_status(self, value: bool):
        if self._expected is not None:
            if self._expected != value:
                print(f"Retry {'ON' if self._expected else 'OFF'}")
                self.switch_callback(switch_on=self._expected)
            else:
                self._expected = None

        self._switch_status = value

    def flick_switch(self, switch_on: bool):
        self._expected = switch_on
        print(f"{'ON' if self._expected else 'OFF'}")
        self._switch_callback(switch_on=switch_on)
