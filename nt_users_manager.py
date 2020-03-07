from typing import List

from loguru import logger

from nt_database import NotetonDatabaseManager
from nt_list import NotetonList
from nt_list_item_article import NotetonListItemArticle
from nt_list_item_file import NotetonListItemFile
from nt_user import NotetonUser


class NotetonUsersManager:
    """
    The main connection class, have information about users, singleton
    """
    instance = None

    # time in seconds, after this time state will change to MAIN_MENU
    time_no_answer = 10

    class __NotetonUsersManager:
        """
        Singleton class for NotetonUsersManager
        """
        def __init__(self):
            self.users = {}
            logger.info('Init NotetonUsersManager')
            self.db = NotetonDatabaseManager()

        def add_user(self, user_id: str, name: str, full_name: str) -> None:
            """
            Add user to manager (or create new one if first time)
            :param user_id: id of user, the same as telegram user id,
            must be string
            :param name: unique user_name from telegram
            :param full_name: full name from telegram
            :return: None, add user to users dict
            """
            user = self.db.get_user(user_id, name, full_name)
            logger.info(f'{user} is added to manager')
            self.users[user_id] = user

    def __init__(self):
        # init singleton
        NotetonUsersManager.init_instance()

    @staticmethod
    def __fix_id_type(id_):
        """
        Fix id if it is not string (it is int from telegram API)
        :param id_: user id, can be int or str
        :return: id as string
        """
        if not isinstance(id_, str):
            id_ = str(id_)
        return id_

    @classmethod
    def init_instance(cls):
        if not cls.instance:
            cls.instance = cls.__NotetonUsersManager()

    @classmethod
    def get_user(cls,
                 user_id: str,
                 name: str = '',
                 full_name: str = '') -> NotetonUser:
        """
        Get user, if user does not exist - create new.
        Request on only user_id, name and full_name need for create new one
        :param user_id: id of user, the same as telegram id
        :param name: user name, from telegram, need only for new users
        :param full_name: full user name, from telegram, need only for new users
        :return: requested user based on user id
        """
        user_id = cls.__fix_id_type(user_id)
        if user_id not in cls.instance.users:
            cls.instance.add_user(user_id, name, full_name)
        return cls.instance.users[user_id]

    @classmethod
    def get_users(cls) -> List[NotetonUser]:
        """
        Get all users from database, NB: expensive operation, it is used only
        for statistic request from admins
        :return: list of users
        """
        return cls.instance.db.get_users()

    @classmethod
    def add_list_to_user(cls, user_id: str, nt_list: NotetonList):
        """
        Create new list for user
        :param user_id: user id, the same as telegram id
        :param nt_list: list which will be added to user
        :return: None
        """
        user_id = cls.__fix_id_type(user_id)
        cls.instance.db.create_list(user_id, nt_list)

    @classmethod
    def get_lists_of_user(cls, user_id: str) -> List[NotetonList]:
        user_id = cls.__fix_id_type(user_id)
        return cls.instance.db.get_lists_of_user(user_id)

    @classmethod
    def change_list_name(cls, user_id: str, nt_list: NotetonList):
        user_id = cls.__fix_id_type(user_id)
        return cls.instance.db.create_list(user_id, nt_list)

    @classmethod
    def delete_list(cls, user_id: str, nt_list: NotetonList):
        user_id = cls.__fix_id_type(user_id)
        return cls.instance.db.delete_list(user_id, nt_list.id)

    @classmethod
    def delete_list_item(cls, list_id: str, item_id: str):
        list_id = cls.__fix_id_type(list_id)
        item_id = cls.__fix_id_type(item_id)
        return cls.instance.db.delete_list_item(list_id, item_id)

    @classmethod
    def get_list_of_user_by_name(cls,
                                 user_id: str,
                                 list_name: str) -> NotetonList:
        nt_lists = NotetonUsersManager.get_lists_of_user(user_id)
        for nt_list in nt_lists:
            if nt_list.list_name == list_name:
                return nt_list

    @classmethod
    def get_lists_of_user_by_type(cls, user_id: str, list_type):
        nt_lists = NotetonUsersManager.get_lists_of_user(user_id)
        filtered_list = list(filter(lambda x: x.type == list_type, nt_lists))
        return filtered_list

    @classmethod
    def add_file_to_list(cls, item: NotetonListItemFile):
        """
        Add file to database
        :param item: item to add
        :return: response from db
        """
        return cls.instance.db.add_item(item)

    @classmethod
    def add_article_to_list(cls, item: NotetonListItemArticle):
        return cls.instance.db.add_item(item)

    @classmethod
    def get_items_of_list(cls, user_id, nt_list: NotetonList):
        return cls.instance.db.get_items_of_list(user_id, nt_list)

