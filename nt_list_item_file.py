from nt_list_item import NotetonListItem


class NotetonListItemFile(NotetonListItem):
    def __init__(self, user_id,
                 list_id=None,
                 id_=None,
                 file_id=None,
                 title=None):
        super().__init__(user_id, list_id, id_)
        self.file_id = file_id
        self.title = title

    def to_dict(self):
        dict_ = {'list_id': self.list_id,
                 'user_id': self.user_id,
                 'item_id': str(self.id),
                 'file_id': self.file_id,
                 'title': self.title}
        return dict_

