import logging
from typing import Tuple

from telegram import InlineKeyboardMarkup

from nt_list import NotetonList
from nt_list_item_article import NotetonListItemArticle
from nt_state import NotetonState
from nt_user import NotetonUser
from nt_users_manager import NotetonUsersManager
from telegram_buttons import generate_lists_buttons, \
    generate_button_with_one_list

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger('NOTETON PROCESS STATE')


def process_delete_list_state(text: str, user: NotetonUser):
    list_name = text[:len(text) - len(NotetonList.DELETE_COMMAND)]
    user.tmp_list = NotetonUsersManager.get_list_of_user_by_name(user.id,
                                                                 list_name)
    result = False
    if user.tmp_list is None:
        logger.error(f'list {list_name} of user {user} not '
                     f'found in process_delete_list_command')
        msg = f'I guess you are trying to delete nonexistent list 🤔'
    else:
        user.set_state(NotetonState.MAIN_MENU)
        res = NotetonUsersManager.delete_list(user.id, user.tmp_list)
        if res['ResponseMetadata']['HTTPStatusCode'] == 200:
            msg = f'list {list_name} has been deleted'
            result = True
        else:
            logger.warning(f'Problem with deleting {list_name} of user '
                           f'{user}, resp code is '
                           f'{res["ResponseMetadata"]["HTTPStatusCode"]}')
            msg = f'Something bad happened, we will check it!'
    return msg, result


def process_add_file_state(text: str, user: NotetonUser):
    lists = NotetonUsersManager.get_lists_of_user(user.id)
    if text in [x.list_name for x in lists]:
        list_ = NotetonUsersManager.get_list_of_user_by_name(user.id, text)
        user.tmp_item.list_id = list_.id
        NotetonUsersManager.add_file_to_list(user.tmp_item)
        user.set_state(NotetonState.MAIN_MENU)
        return f'File added to list {text}, you can get whole list via ' \
               f'@noteton_bot {text} or press button below', True

    else:
        return f'Wrong list, please, use buttons', False


def process_add_article_state(text: str, user: NotetonUser):
    lists = NotetonUsersManager.get_lists_of_user(user.id)
    if text in [x.list_name for x in lists]:
        list_ = NotetonUsersManager.get_list_of_user_by_name(user.id, text)
        user.tmp_item.list_id = list_.id
        NotetonUsersManager.add_article_to_list(user.tmp_item)
        user.set_state(NotetonState.MAIN_MENU)
        return f'Article added to list {text}, you can get whole list via ' \
               f'@noteton_bot {text}', True

    else:
        return f'Wrong list, please, use buttons', False


def process_create_list_state(text: str, user: NotetonUser):
    types = NotetonList.get_types()
    if text in types:
        user.tmp_list.type = text
        NotetonUsersManager.add_list_to_user(user.id, user.tmp_list)
        user.set_state(NotetonState.MAIN_MENU)
        return f'I created new list for you: {user.tmp_list.list_name}', True
    else:
        return 'Wrong type, please, use buttons', False


def process_edit_list_state(text: str, user: NotetonUser):
    list_name = text[:len(text) - len(NotetonList.EDIT_COMMAND)]
    user.tmp_list = NotetonUsersManager.get_list_of_user_by_name(user.id,
                                                                 list_name)
    user.set_state(NotetonState.EDIT_LIST)
    return f'Send me new name for list {list_name}'


def process_feedback(username: str,
                     full_name: str,
                     text: str,
                     user: NotetonUser):
    """
    Process feedback command
    :param username: user username from telegram
    :param full_name: user full name from telegram
    :param text: feedback message
    :param user: current user
    :return: Answer to user, change user state to MAIN_MENU
    """
    feedback_text = f'******FEEDBACK*******\n' \
                    f'from user {user} with username ' \
                    f'{username} and fullname ' \
                    f'{full_name}:\n{text}'
    user.set_state(NotetonState.MAIN_MENU)
    return 'Message has been sent, thank you!', feedback_text


def process_edit_list(new_list_name: str,
                      user: NotetonUser):
    """
    Process editing list, currently only name can be changed
    :param new_list_name: new list name
    :param user: current user
    :return: message will be send to user, change user state to MAIN_MENU
    """
    nt_lists = NotetonUsersManager.get_lists_of_user(user.id)
    names = [x.list_name for x in nt_lists]
    val_result, msg = NotetonList.validate_list_name(new_list_name, names)
    if val_result:
        user.set_state(NotetonState.MAIN_MENU)
        user.tmp_list.list_name = new_list_name
        NotetonUsersManager.change_list_name(user.id,
                                             user.tmp_list)

        msg = None
    return msg, val_result


def process_create_list(list_name, user):
    """
    Process create list logic
    :param list_name: list name
    :param user: current user
    :return: None, change user state to CREATE_LIST_TYPE and send invite
             to choosing list type
    """
    nt_lists = NotetonUsersManager.get_lists_of_user(user.id)
    names = [x.list_name for x in nt_lists]
    val_result, msg = NotetonList.validate_list_name(list_name, names)
    if val_result:
        user.tmp_list = NotetonList(user.id, list_name)
        user.set_state(NotetonState.CREATE_LIST_TYPE)
        msg = 'Choose the type of list:'
    return msg, val_result


def process_text_message_main_menu(user: NotetonUser,
                                   text: str) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Process state when user send text message to bot to add in article list
    :param user: current user
    :param text: current potential item (text, links, etc.)
    :return: msg to user, buttons with article list;
    :side_effects: change user state to ADD_ARTICLE, request to db (get_lists)
    """
    user.tmp_item = NotetonListItemArticle(user_id=user.id,
                                           text=text)
    lists = NotetonUsersManager.get_lists_of_user_by_type(user.id,
                                                          NotetonList.TYPE_ARTICLE)
    if not lists:
        msg = 'Oops, you have no lists with articles, ' \
               'please, create at least one first'
        reply_markup = None
    elif len(lists) == 1:
        msg, result = process_add_file_state(lists[0].list_name, user)
        reply_markup = generate_button_with_one_list(lists[0].list_name)
        if result:
            user.set_state(NotetonState.MAIN_MENU)
    else:
        msg = 'Choose the list:'
        reply_markup = generate_lists_buttons(lists)
        user.set_state(NotetonState.ADD_ARTICLE)

    return msg, reply_markup
