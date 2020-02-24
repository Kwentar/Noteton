from nt_list_item import NotetonListItem


class NotetonListItemPhoto(NotetonListItem):
    def __init__(self, user_id,
                 list_id=None,
                 id_=None,
                 file_id=None,
                 key=None,
                 obj=None):
        super().__init__(user_id, list_id, id_)
        self.file_id = file_id
        self.key = key
        self.obj = obj

    def to_dict(self):
        dict_ = {'list_id': self.list_id,
                 'user_id': self.user_id,
                 'item_id': str(self.id),
                 'file_id': self.file_id,
                 'key': self.key}
        return dict_

    def generate_key(self):
        self.key = f'{self.user_id}/{self.list_id}/{self.id}.jpg'
