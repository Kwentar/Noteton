from typing import List
from uuid import uuid4


class NotetonList:
    """
    Noteton list represents user list, main properties: name (list name,
    created by user) and type - one of possible types,
    user choose it via buttons
    """

    TYPE_IMAGE = 'type_images'
    TYPE_ARTICLE = 'type_articles'
    TYPE_STICKER = 'type_stickers'
    TYPE_GIF = 'type_gifs'
    TYPE_AUDIO = 'type_audios'
    TYPE_DOCUMENT = 'type_documents'

    EDIT_COMMAND = '*edit*'
    DELETE_COMMAND = '*delete*'
    DELETE_ITEM_COMMAND = '*delete_item*'

    @classmethod
    def get_types(cls) -> List[str]:
        """
        Get current possible types of list
        :return: list of types
        """
        return [cls.TYPE_IMAGE, cls.TYPE_ARTICLE, cls.TYPE_STICKER,
                cls.TYPE_GIF, cls.TYPE_AUDIO, cls.TYPE_DOCUMENT]

    def __init__(self, user_id: str,
                 list_name: str,
                 id_: str = None,
                 type_: str = TYPE_IMAGE):
        """
        :param user_id: list owner id, the same as telegram id
        :param list_name: name of list
        :param id_: list id, if None it will be generated
        :param type_: type of list
        """
        self.user_id = user_id
        self.list_name = list_name
        if id_ is None:
            id_ = str(uuid4())
        self.id = id_

        self.type = type_

    def __repr__(self):
        return f'{self.user_id}\'s list {self.list_name}, type: {self.type}'

    @staticmethod
    def validate_list_name(list_name: str, user_lists: List[str]):
        """
        Validate list name, conditionals:
        * list_name must be not empty and less than 20 symbols
        * list_name must be unique in account, so, not be in user_lists
        * list name must contains only letters, numbers and underscore
        :param list_name: potential list name, which one will be validated
        :param user_lists: current lists of user
        :return: True and 'OK' if name is ok and False and error message if not
        """

        if list_name in user_lists:
            return False, 'You already have list with this name'
        if len(list_name) >= 20 or not list_name:
            return False, 'Name of list should be at least 1 symbol ' \
                          'and less than 20'

        words = list_name.split('_')
        for word in words:
            if not word.isalnum():
                return False, 'Wrong symbols, only letters, ' \
                              'numbers and underscore _'

        return True, 'Ok'


if __name__ == '__main__':
    assert NotetonList.validate_list_name('test', [])[0]
    assert NotetonList.validate_list_name('test_list', [])[0]
    assert NotetonList.validate_list_name('test13_number', [])[0]
    assert not NotetonList.validate_list_name('test test', [])[0]
    assert not NotetonList.validate_list_name('', [])[0]
    assert not NotetonList.validate_list_name('test-223e2', [])[0]
    assert NotetonList.validate_list_name('выаыва', [])[0]
    assert not NotetonList.validate_list_name('test', ['test', 'tmp'])[0]
    assert not NotetonList.validate_list_name('awewqddfwefwfwefedfsfsd', [])[0]
    assert not NotetonList.validate_list_name('88888*', [])[0]

