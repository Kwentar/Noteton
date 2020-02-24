from datetime import datetime

from nt_list import NotetonList
from nt_list_item import NotetonListItem
from nt_state import NotetonState


class NotetonUser:
    def __init__(self, user_id):
        self.user_id = user_id
        self.registration_date = datetime.now()
        self.state = NotetonState()
        self.tmp_list = NotetonList('-1', '123')
        self.tmp_item = NotetonListItem(user_id)

    def convert_user_to_dict(self):
        return {'user_id': self.user_id,
                'registration_date': str(self.registration_date)}

    def setup_registration_date_from_string(self, value):
        self.registration_date = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')

    def get_state(self):
        return self.state.get_state()

    def set_state(self, state):
        self.state.set_state(state)

    def __repr__(self):
        return f'user {self.user_id} registered {self.registration_date}'
