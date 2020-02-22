class NotetonState:
    MAIN_MENU = 0
    MAIN_LIST = 1
    SUBLIST = 2
    INFO = 3
    CREATE_LIST = 10
    EDIT_LIST = 11

    NAME_TO_STR = {
        MAIN_MENU: 'MAIN_MENU',
        MAIN_LIST: 'MAIN_LIST',
        SUBLIST: 'SUBLIST',
        INFO: 'INFO',
        CREATE_LIST: 'CREATE_LIST',
        EDIT_LIST: 'EDIT_LIST'
    }

    instance = None

    class __NotetonState:
        def __init__(self, state):
            self.state = state

        def __str__(self):
            return f'current state: {NotetonState.NAME_TO_STR[self.state]}'

    def __init__(self):
        NotetonState.init_instance()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    @staticmethod
    def init_instance():
        if not NotetonState.instance:
            NotetonState.instance = \
                NotetonState.__NotetonState(NotetonState.MAIN_MENU)

    @staticmethod
    def change_state(state):
        NotetonState.init_instance()
        NotetonState.instance.state = state

    @staticmethod
    def get_state():
        NotetonState.init_instance()
        return NotetonState.instance.state
