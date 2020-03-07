from loguru import logger


class NotetonState:
    """
    Class represents user state for bot
    """
    MAIN_MENU = 'MAIN_MENU'
    MAIN_LIST = 'MAIN_LIST'
    SUBLIST = 'SUBLIST'
    INFO = 'INFO'
    CREATE_LIST_NAME = 'CREATE_LIST_NAME'
    CREATE_LIST_TYPE = 'CREATE_LIST_TYPE'
    EDIT_LIST = 'EDIT_LIST'
    DELETE_LIST = 'DELETE_LIST'
    FEEDBACK = 'FEEDBACK'
    ADD_FILE = 'ADD_FILE'
    ADD_ARTICLE = 'ADD_ARTICLE'
    NO_ANSWER = 'NO_ANSWER'
    DELETE_ITEM = 'DELETE_ITEM'

    states = None

    def __init__(self):
        self.state = NotetonState.MAIN_MENU
        if NotetonState.states is None:
            NotetonState.states = \
                [x for x in NotetonState.__dict__ if x.isupper()]

    def set_state(self, state: str):
        if state not in NotetonState.states:
            logger.error(f'state {state} not in NotetonState.states')
        self.state = state

    def get_state(self):
        return self.state
