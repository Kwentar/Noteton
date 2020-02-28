class NotetonState:
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

    def __init__(self):
        self.state = NotetonState.MAIN_MENU

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state
