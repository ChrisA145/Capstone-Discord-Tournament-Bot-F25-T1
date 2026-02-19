
class ButtonState:
    def __init__(self):
        self.buttons_state : bool = None

    def set_button_state(self, value: bool):
        self.buttons_state = value

    def reset_button_state(self):
        self.buttons_state = None

first_login_users = {}
