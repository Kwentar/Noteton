from nt_list_item import NotetonListItem


class NotetonListItemArticle(NotetonListItem):
    def __init__(self, user_id,
                 list_id=None,
                 id_=None,
                 text=None):
        super().__init__(user_id, list_id, id_)
        self.text = text

    def to_dict(self):
        dict_ = {'list_id': self.list_id,
                 'user_id': self.user_id,
                 'item_id': str(self.id),
                 'text': self.text}
        return dict_
