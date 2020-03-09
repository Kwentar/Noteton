from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key

from nt_list import NotetonList
from nt_list_item import NotetonListItem
from nt_list_item_article import NotetonListItemArticle
from nt_list_item_file import NotetonListItemFile
from nt_user import NotetonUser


class NotetonDatabaseManager:
    """
    Database (dynamodb) manager
    """
    def __init__(self, region_name='eu-central-1'):
        """
        We have 3 tables:
        NotetonUser, which one represents telegram user in bot context;
        NotetonList, which one represents user list;
        NotetonListItem, which one represents item of user list
        :param region_name: region_name in AWS context, where dynamodb is hosted
        """
        self.db = boto3.resource('dynamodb', region_name=region_name)
        self.users_table = self.db.Table('NotetonUser')
        self.list_table = self.db.Table('NotetonList')
        self.list_item_table = self.db.Table('NotetonListItem')

    def get_user(self, user_id: str) -> Optional[NotetonUser]:
        """
        Get user by user id (the same as telegram id)
        :param user_id: user id, the same as telegram user id
        :return:
        """
        response = self.users_table.get_item(Key={'user_id': user_id})

        if 'Item' in response:
            item = response['Item']
            user = NotetonUser(user_id=user_id)
            user.setup_registration_date_from_string(item['registration_date'])
            user.name = item['user_name']
            user.full_name = item['full_name']
            return user
        else:
            return response

    def add_new_user(self, user: NotetonUser):
        """
        Add new user to database
        :param user: user which one is being added
        :return: None
        """
        response = self.users_table.put_item(Item=user.convert_user_to_dict())
        return response

    def get_users(self) -> List[NotetonUser]:
        """
        Get all users from database, NB: expensive operation, use only for stat
        :return: list of NotetonUser
        """
        response = self.users_table.scan()
        users = []
        if 'Items' in response:
            for item in response['Items']:
                user = NotetonUser(user_id=item['user_id'],
                                   user_name=item['user_name'],
                                   full_name=item['full_name'])
                user.setup_registration_date_from_string(
                    item['registration_date']
                )
                users.append(user)

            return users
        return response

    def create_list(self, user_id: str, nt_list: NotetonList):
        list_dictionary = {'user_id': user_id,
                           'list_id': nt_list.id,
                           'list_name': nt_list.list_name,
                           'list_type': nt_list.type}
        return self.list_table.put_item(Item=list_dictionary)

    def get_lists_of_user(self, user_id: str) -> List[NotetonList]:
        """
        Get all lists of user with user_id
        :param user_id: user id (telegram id)
        :return: lists of NotetonList of user
        """
        result = self.list_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id))
        items = result['Items']
        nt_lists = []
        for item in items:
            nt_list = NotetonList(user_id, item['list_name'],
                                  item['list_id'], item['list_type'])
            nt_lists.append(nt_list)
        return nt_lists

    def delete_list(self, user_id, list_id):
        """
        Delete list if user and all items of list
        :param user_id: requested user id
        :param list_id: requested list id
        :return: response, will be fixed
        """
        items = self.list_item_table.query(
            KeyConditionExpression=Key('list_id').eq(list_id))['Items']
        for item in items:
            self.delete_list_item(list_id, item['item_id'])
        response = self.list_table.delete_item(Key={'user_id': user_id,
                                                    'list_id': list_id})
        return response

    def delete_list_item(self, list_id, item_id):
        """
        Delete one item from list
        :param list_id: requested list_id
        :param item_id: requested item_id
        :return: response, will be fixed
        """
        response = self.list_item_table.delete_item(Key={'list_id': list_id,
                                                         'item_id': item_id})
        return response

    def add_list_item(self, item: NotetonListItem):
        """
        Add item to list_item_table
        :param item: item is being added
        :return: response, will be fixed
        """
        response = self.list_item_table.put_item(Item=item.to_dict())

        return response

    def get_items_of_list(self, user_id: str, nt_list: NotetonList) \
            -> List[NotetonListItem]:
        """
        Get all items of user list
        :param user_id: requested user id, the same as telegram id
        :param nt_list: requested NotetonList
        :return: List of items of current NotetonList
        """
        result = self.list_item_table.query(
            KeyConditionExpression=Key('list_id').eq(nt_list.id))

        items = result['Items']
        nt_items = []
        for item in items:
            nt_item = None
            if nt_list.type in [NotetonList.TYPE_IMAGE,
                                NotetonList.TYPE_STICKER,
                                NotetonList.TYPE_GIF,
                                NotetonList.TYPE_AUDIO,
                                NotetonList.TYPE_DOCUMENT]:
                nt_item = NotetonListItemFile(user_id=user_id,
                                              list_id=nt_list.id,
                                              id_=item['item_id'],
                                              file_id=item['file_id'])
                if 'title' in item:
                    nt_item.title = item['title']
            elif nt_list.type == NotetonList.TYPE_ARTICLE:
                nt_item = NotetonListItemArticle(user_id=user_id,
                                                 list_id=nt_list.id,
                                                 id_=item['item_id'],
                                                 text=item['text'])
            if nt_item is not None:
                nt_items.append(nt_item)
        return nt_items
