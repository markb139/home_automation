class SwitchHandler:
    def __init__(self, switch_callback=None):
        self._switch_status = None
        self._expected = None
        self._switch_callback = switch_callback

    @property
    def switch_callback(self):
        return self._switch_callback

    @switch_callback.setter
    def switch_callback(self, callback):
        self._switch_callback = callback

    # @property
    # def is_trying(self):
    #     return (self._expected is not None) and self._expected != self._switch_status

    # @property
    # def switch_status(self):
    #     return self._switch_status

    # @switch_status.setter
    def switch_status(self, value: bool):
        print(f"switch_status:set {value}")
        if self._expected is not None:
            if self._expected != value:
                if self.switch_callback:
                    print(f"Retry {'ON' if self._expected else 'OFF'}")
                    self.switch_callback(switch_on=self._expected)
            else:
                self._expected = None

        self._switch_status = value

    def flick_switch(self, switch_on: bool):
        print(f"flick_switch {switch_on}")
        self._expected = switch_on
        if self._switch_callback:
            self._switch_callback(switch_on=switch_on)
