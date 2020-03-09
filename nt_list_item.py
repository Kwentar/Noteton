from uuid import uuid4


class NotetonListItem:
    def __init__(self, user_id, list_id=None, id_=None):
        self.user_id = user_id
        self.list_id = list_id
        if id_ is None:
            id_ = uuid4()
        self.id = id_

    def to_dict(self):
        pass
