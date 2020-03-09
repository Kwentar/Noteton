from datetime import datetime
from loguru import logger
from nt_list import NotetonList
from nt_list_item import NotetonListItem
from nt_state import NotetonState


class NotetonUser:
    """
    Class represents user who communicate with bot. All personal information
    like id, name and fullname is from telegram. Class responsible for
    user info, user state (see NotetonState) and conversion to database view
    """
    def __init__(self, user_id: str,
                 user_name: str = None,
                 full_name: str = None):
        """
        User object initialization, NB: user_id should be string, but
        NotetonUsersManager object will fix it if user_id is int
        (see NotetonUsersManager.__fix_id_type)
        :param user_id: user id == user telegram id
        :param user_name: unique user name, from telegram
        :param full_name: user full name, from telegram
        """
        self.id = user_id
        self.registration_date = datetime.now()
        self.state = NotetonState()
        self.tmp_list = NotetonList('-1', '123')
        self.tmp_item = NotetonListItem(user_id)
        self.lists_message_id = None
        self.time_inline = None
        self.name = user_name
        self.full_name = full_name

    def convert_user_to_dict(self):
        """
        Convert user to python dict, this method is used in database writing
        :return: dict of user
        """
        return {'user_id': self.id,
                'registration_date': str(self.registration_date),
                'user_name': str(self.name),
                'full_name': str(self.full_name)}

    def setup_registration_date_from_string(self, source_datetime: str) -> None:
        """
        Convert date from database string format to python datetime
        :param source_datetime: source datetime
        :return: None, change registration date of user
        """
        self.registration_date = datetime.strptime(source_datetime,
                                                   '%Y-%m-%d %H:%M:%S.%f')

    def get_state(self) -> str:
        """
        Proxy-method from State.get_state, the same as user.state.get_state
        :return: state of user
        """
        return self.state.get_state()

    def set_state(self, state: str) -> None:
        """
        Proxy-method for State.set_state, the same as user.state.set_state
        :param state: new state of user
        :return: None, change user state
        """
        logger.info(f'State of {self} changed: {self.get_state()} -> {state}')
        self.state.set_state(state)

    def __repr__(self):
        return f'user {self.id} {self.name} {self.full_name}'
