from typing import List

import boto3

from boto3.dynamodb.conditions import Key, Attr

from nt_list import NotetonList
from nt_user import NotetonUser


class NotetonDatabaseManager:
    def __init__(self):
        # self.client = boto3.client('dynamodb', region_name='eu-central-1')
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
        response = self.list_table.delete_item(Key={'user_id': user_id,
                                                    'list_id': list_id})
        return response


if __name__ == '__main__':
    db_manager = NotetonDatabaseManager()
    res = db_manager.get_lists_of_user('2223')
    print('finish')
