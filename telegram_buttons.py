from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup

from nt_list import NotetonList


def generate_list_types_buttons():
    """
    Generate buttons with types of list (on the create list step)
    :return: Inline markup with buttons, one button per type
    """
    button_list = []
    for type_ in NotetonList.get_types():
        button = [InlineKeyboardButton(type_.split('_')[1].capitalize(),
                                       callback_data=type_)]
        button_list.append(button)
    reply_markup = InlineKeyboardMarkup(button_list)
    return reply_markup


def generate_lists_buttons(nt_lists):
    """
    Generate buttons with list (on the "choose list for item" step
    :param nt_lists: lists of user, filtered by type
    :return: Inline markup with buttons, one button per list
    """
    button_list = []
    for list_ in nt_lists:
        button = [InlineKeyboardButton(list_.list_name,
                                       callback_data=list_.list_name)]
        button_list.append(button)
    reply_markup = InlineKeyboardMarkup(button_list)
    return reply_markup


def generate_button_with_one_list(list_name: str) -> InlineKeyboardMarkup:
    """
    Generate button for case when user has only one list with this type
    :param list_name:
    :return: InlineKeyboardMarkup with one button (list is called list_name)
    """
    buttons = [
        [InlineKeyboardButton(list_name,
                              switch_inline_query_current_chat=list_name)]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    return reply_markup


def generate_buttons_my_lists(nt_lists):
    """
    Generate buttons for the my list command
    :param nt_lists: All user lists
    :return: Inline markup grid with size len(nt_lists)X3,
             one row per list with edit and delete buttons
    """
    button_list = []
    edit = NotetonList.EDIT_COMMAND
    delete = NotetonList.DELETE_COMMAND
    del_item = NotetonList.DELETE_ITEM_COMMAND
    for nt_list in nt_lists:
        name = nt_list.list_name
        button = [InlineKeyboardButton(name,
                                       switch_inline_query_current_chat=name),
                  InlineKeyboardButton('✏',
                                       callback_data=f'{name}{edit}'),
                  InlineKeyboardButton('❌',
                                       callback_data=f'{name}{delete}'),
                  InlineKeyboardButton('❌ item',
                                       switch_inline_query_current_chat=f'{name}{del_item}')
                  ]
        button_list.append(button)
    reply_markup = InlineKeyboardMarkup(button_list)
    return reply_markup


def generate_main_menu():
    """
    Generate main menu
    :return: Reply markup with buttons, one button per menu item
    """
    buttons = [['Main menu'],
               ['Create list'],
               ['My lists'],
               ['Info & Help'],
               ['Send feedback']]

    reply_markup = ReplyKeyboardMarkup(buttons)
    return reply_markup



