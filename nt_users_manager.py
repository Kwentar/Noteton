from typing import List

from nt_database import NotetonDatabaseManager
from nt_list import NotetonList
from nt_user import NotetonUser


class NotetonUsersManager:

    instance = None

    class __NotetonUsersManager:
        def __init__(self):
            self.users = {}
            self.db = NotetonDatabaseManager()

        def __str__(self):
            return f'NotetonUsersManager'

        def add_user(self, user_id):
            user = self.db.get_user(user_id)
            self.users[user_id] = user

    def __init__(self):
        NotetonUsersManager.init_instance()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    @staticmethod
    def __fix_user_id(user_id):
        if not isinstance(user_id, str):
            user_id = str(user_id)
        return user_id

    @classmethod
    def init_instance(cls):
        if not cls.instance:
            cls.instance = cls.__NotetonUsersManager()

    @classmethod
    def get_user(cls, user_id: str) -> NotetonUser:
        user_id = cls.__fix_user_id(user_id)
        if user_id not in cls.instance.users:
            cls.instance.add_user(user_id)
        return cls.instance.users[user_id]

    @classmethod
    def add_list_to_user(cls, user_id: str, nt_list: NotetonList):
        user_id = cls.__fix_user_id(user_id)
        cls.instance.db.create_list(user_id, nt_list)

    @classmethod
    def get_lists_of_user(cls, user_id: str) -> List[NotetonList]:
        user_id = cls.__fix_user_id(user_id)
        return cls.instance.db.get_lists_of_user(user_id)

    @classmethod
    def change_list_name(cls, user_id: str, nt_list: NotetonList):
        user_id = cls.__fix_user_id(user_id)
        return cls.instance.db.create_list(user_id, nt_list)

    @classmethod
    def delete_list(cls, user_id: str, nt_list: NotetonList):
        user_id = cls.__fix_user_id(user_id)
        return cls.instance.db.delete_list(user_id, nt_list.id)

    @classmethod
    def get_list_of_user_by_name(cls,
                                 user_id: str,
                                 list_name: str) -> NotetonList:
        nt_lists = NotetonUsersManager.get_lists_of_user(user_id)
        for nt_list in nt_lists:
            if nt_list.list_name == list_name:
                return nt_list


