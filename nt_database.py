from typing import List

import boto3

from boto3.dynamodb.conditions import Key, Attr

from nt_list import NotetonList
from nt_list_item_article import NotetonListItemArticle
from nt_list_item_file import NotetonListItemFile
from nt_user import NotetonUser


class NotetonDatabaseManager:
    def __init__(self):
        self.db = boto3.resource('dynamodb', region_name='eu-central-1')
        self.users_table = self.db.Table('NotetonUser')
        self.list_table = self.db.Table('NotetonList')
        self.list_item_table = self.db.Table('NotetonListItem')

    def get_user(self, user_id):
        if type(user_id) != str:
            user_id = str(user_id)
        response = self.users_table.get_item(Key={'user_id': user_id})
        user = NotetonUser(user_id=user_id)

        if 'Item' not in response:
            self.users_table.put_item(Item=user.convert_user_to_dict())
        else:
            item = response['Item']
            user.setup_registration_date_from_string(item['registration_date'])
        return user

    def create_list(self, user_id: str, nt_list: NotetonList):
        list_dictionary = {'user_id': user_id,
                           'list_id': nt_list.id,
                           'list_name': nt_list.list_name,
                           'list_type': nt_list.type}
        self.list_table.put_item(Item=list_dictionary)

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

    def delete_item(self, table_name, pk_name, pk_value):
        """
        Delete an item (row) in table from its primary key.
        """
        table = self.db.Table(table_name)
        response = table.delete_item(Key={pk_name: pk_value})

        return response

    def delete_list(self, user_id, list_id):
        items = self.list_item_table.query(
            KeyConditionExpression=Key('list_id').eq(list_id))['Items']
        for item in items:
            self.delete_list_item(list_id, item['item_id'])
        response = self.list_table.delete_item(Key={'user_id': user_id,
                                                    'list_id': list_id})
        return response

    def delete_list_item(self, list_id, item_id):
        response = self.list_item_table.delete_item(Key={'list_id': list_id,
                                                         'item_id': item_id})
        return response

    def add_item(self, item):
        response = self.list_item_table.put_item(Item=item.to_dict())

        return response

    def get_items_of_list(self, user_id, nt_list: NotetonList):
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


if __name__ == '__main__':
    db_manager = NotetonDatabaseManager()
    # res = db_manager.get_items_of_list('177349801',
    #                                    '401203bf-7830-4720-8eb4-a017f659d3b9')
    print('finish')
