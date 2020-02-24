import logging
from datetime import datetime

from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardMarkup, Update, InlineQueryResultPhoto, \
    InlineQueryResultCachedPhoto
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, \
    CallbackQueryHandler, MessageHandler, Filters, CallbackContext

from config import token, god_chat_id
from nt_list import NotetonList
from nt_list_item_photo import NotetonListItemPhoto
from nt_s3_manager import NotetonS3Manager
from nt_state import NotetonState

from nt_users_manager import NotetonUsersManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger('NOTETON MAIN')


def callback_query_handler(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    text = update.callback_query.data
    logger.info(f'message in callback_query {text}')
    if user.get_state() == NotetonState.CREATE_LIST_TYPE:
        types = NotetonList.get_types()
        if text in types:
            user.tmp_list.type = text
            NotetonUsersManager.add_list_to_user(user.user_id, user.tmp_list)
            user.set_state(NotetonState.MAIN_MENU)
            context.bot.send_message(chat_id=chat_id,
                                     text=f'I created new list for you: '
                                          f'{user.tmp_list.list_name}')
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text=f'Wrong type, please, use buttons')
    if user.get_state() == NotetonState.ADDED_PHOTO:
        lists = NotetonUsersManager.get_lists_of_user(user_id)
        if text in [x.list_name for x in lists]:
            list_ = NotetonUsersManager.get_list_of_user_by_name(user_id, text)
            user.tmp_item.list_id = list_.id
            user.tmp_item.generate_key()
            NotetonUsersManager.add_photo_to_list(user.tmp_item)
            user.set_state(NotetonState.MAIN_MENU)
            context.bot.send_message(chat_id=chat_id,
                                     text=f'Images added to list {text}, '
                                          f'you can get whole list via '
                                          f'@noteton_bot {text}')
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text=f'Wrong list, please, use buttons')
    else:
        if text.endswith(NotetonList.EDIT_COMMAND):
            list_name = text[:len(text) - len(NotetonList.EDIT_COMMAND)]
            nt_lists = NotetonUsersManager.get_lists_of_user(user_id)
            for nt_list in nt_lists:
                if nt_list.list_name == list_name:
                    user.tmp_list = nt_list
                    break
            user.set_state(NotetonState.EDIT_LIST)

            context.bot.send_message(chat_id=chat_id,
                                     text=f'Input new name for list '
                                          f'{list_name}:')
        elif text.endswith(NotetonList.DELETE_COMMAND):
            list_name = text[:len(text) - len(NotetonList.DELETE_COMMAND)]
            user.tmp_list = \
                NotetonUsersManager.get_list_of_user_by_name(user_id, list_name)
            if user.tmp_list is None:
                logger.error(f'list {list_name} of user {user_id} not '
                             f'found in delete list')
                context.bot.send_message(chat_id=chat_id,
                                         text=f'I guess you are trying to '
                                              f'delete nonexistent list 🤔')
            else:
                user.set_state(NotetonState.MAIN_MENU)
                res = NotetonUsersManager.delete_list(user_id, user.tmp_list)
                if res['ResponseMetadata']['HTTPStatusCode'] == 200:
                    context.bot.send_message(chat_id=chat_id,
                                             text=f'list {list_name} '
                                                  f'has been deleted')
                else:
                    context.bot.send_message(chat_id=chat_id,
                                             text=f'Something bad happened, '
                                                  f'we will check it!')
                    logger.warning('Problem with deleting {list_name} of user '
                                   '{user_id}, resp code is '
                                   '{res["ResponseMetadata"]["HTTPStatusCode"]}')


def inline_query(update: Update, context: CallbackContext):
    """Handle the inline query."""
    query = update.inline_query.query
    user_id = update.effective_user.id
    nt_list = NotetonUsersManager.get_list_of_user_by_name(user_id, query)
    if nt_list:
        items = NotetonUsersManager.get_items_of_list(user_id, nt_list)
        answer_items = []
        if items:
            for item in items:
                # url = NotetonS3Manager().generate_pre_signed_url(item.key)
                id_ = item.id
                item = InlineQueryResultCachedPhoto(id=id_, photo_file_id=item.file_id)
                answer_items.append(item)
        update.inline_query.answer(answer_items, cache_time=5, is_personal=True,
                                   timeout=300)


def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    logger.info(f'I have new message: {text} from {user_id}')

    if user.get_state() == NotetonState.MAIN_MENU:
        if text == 'Create list':
            create_list(update, context)
        elif text == 'My lists':
            my_lists(update, context)
        elif text == 'Info & Help':
            info_and_help(update, context)
        elif text == 'Send feedback':
            feedback(update, context)
    elif user.get_state() == NotetonState.CREATE_LIST_NAME:

        nt_lists = NotetonUsersManager.get_lists_of_user(user_id)
        names = [x.list_name for x in nt_lists]
        val_result, message = NotetonList.validate_list_name(text, names)

        if val_result:
            user.tmp_list = NotetonList(user_id, text)
            user.set_state(NotetonState.CREATE_LIST_TYPE)

            types = NotetonList.get_types()
            button_list = []

            for type_ in types:
                button = [InlineKeyboardButton(type_.split('_')[1].capitalize(),
                                               callback_data=type_)]
                button_list.append(button)
            reply_markup = InlineKeyboardMarkup(button_list)

            context.bot.send_message(chat_id=chat_id,
                                     text=f'Choose the type of list:',
                                     reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text=message)
    elif user.get_state() == NotetonState.EDIT_LIST:
        nt_lists = NotetonUsersManager.get_lists_of_user(user_id)
        names = [x.list_name for x in nt_lists]
        val_result, message = NotetonList.validate_list_name(text, names)

        if val_result:
            user.set_state(NotetonState.MAIN_MENU)
            user.tmp_list.list_name = text
            NotetonUsersManager.change_list_name(user_id,
                                                 user.tmp_list)
            context.bot.send_message(chat_id=chat_id,
                                     text=f'The list name has been changed ✅')
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text=message)
    elif user.get_state() == NotetonState.FEEDBACK:
        feedback_text = f'******FEEDBACK*******\n' \
                        f'from user {user_id} with username ' \
                        f'{update.effective_user.username} and fullname ' \
                        f'{update.effective_user.full_name}:\n{text}'
        context.bot.send_message(chat_id=god_chat_id, text=feedback_text)
        context.bot.send_message(chat_id=chat_id, text='Message has been sent, '
                                                       'thank you!')
        user.set_state(NotetonState.MAIN_MENU)

    # context.bot.send_message(chat_id=chat_id,
    #                          text=f'I have new message: {text}')


def photo_handler(update: Update, context: CallbackContext):
    photo_id = update.message.photo[-1].file_id
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    new_file = context.bot.get_file(photo_id)
    byte_array = new_file.download_as_bytearray()
    item = NotetonListItemPhoto(user_id=user_id,
                                file_id=photo_id,
                                obj=byte_array)

    user = NotetonUsersManager.get_user(user_id)
    user.tmp_item = item
    user.set_state(NotetonState.ADDED_PHOTO)
    lists = NotetonUsersManager.get_lists_of_user_by_type(user_id,
                                                          NotetonList.TYPE_IMAGES)
    if not lists:
        context.bot.send_message(chat_id=chat_id,
                                 text=f'Oops, you have no lists with images,'
                                      f'please, create at least one first')
        return
    button_list = []
    for list_ in lists:
        button = [InlineKeyboardButton(list_.list_name,
                                       callback_data=list_.list_name)]
        button_list.append(button)
    reply_markup = InlineKeyboardMarkup(button_list)

    context.bot.send_message(chat_id=chat_id,
                             text=f'Choose the list:',
                             reply_markup=reply_markup)


def start(update: Update, context: CallbackContext):
    logger.info(f'I have start command')

    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)

    user.set_state(NotetonState.MAIN_MENU)
    buttons = [['Create list'], ['My lists'],
               ['Info & Help'], ['Send feedback']]

    reply_markup = ReplyKeyboardMarkup(buttons)

    context.bot.send_message(chat_id=chat_id,
                             text='Main menu:\n'
                                  '/create_list \n'
                                  '/my_lists\n'
                                  '/info_and_help\n'
                                  '/send_feedback',
                             reply_markup=reply_markup)


def create_list(update: Update, context: CallbackContext):
    logger.info(f'I have create_list command')

    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    user.set_state(NotetonState.CREATE_LIST_NAME)
    context.bot.send_message(chat_id=chat_id,
                             text='Send me name of list (less than 20 symbols,'
                                  ' letters, numbers and underscore _)')


def my_lists(update: Update, context: CallbackContext):
    logger.info(f'I have my_lists command')
    chat_id = update.message.chat_id
    user_id = update.effective_user.id

    nt_lists = NotetonUsersManager.get_lists_of_user(user_id)
    button_list = []
    edit = NotetonList.EDIT_COMMAND
    delete = NotetonList.DELETE_COMMAND
    for nt_list in nt_lists:
        name = nt_list.list_name
        button = [InlineKeyboardButton(name,
                                       switch_inline_query_current_chat=name),
                  InlineKeyboardButton('edit',
                                       callback_data=f'{name}{edit}'),
                  InlineKeyboardButton('delete',
                                       callback_data=f'{name}{delete}')
                  ]
        button_list.append(button)
    reply_markup = InlineKeyboardMarkup(button_list)

    context.bot.send_message(chat_id=chat_id,
                             text=f'Your lists:',
                             reply_markup=reply_markup)


def info_and_help(update: Update, context: CallbackContext):
    logger.info(f'I have info_and_help command')

    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id,
                             text=f'I have command info_and_help')


def feedback(update: Update, context: CallbackContext):
    logger.info(f'I have feedback command')
    user_id = update.effective_user.id
    NotetonUsersManager.get_user(user_id).set_state(NotetonState.FEEDBACK)
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id,
                             text=f'Send feedback message:')


def main():
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("create_list", create_list))
    dp.add_handler(CommandHandler("my_lists", my_lists))
    dp.add_handler(CommandHandler("info_and_help", info_and_help))
    dp.add_handler(CommandHandler("send_feedback", feedback))
    dp.add_handler(CommandHandler("help", info_and_help))

    dp.add_handler(InlineQueryHandler(inline_query))
    dp.add_handler(CallbackQueryHandler(callback_query_handler))
    dp.add_handler(MessageHandler(Filters.text, message_handler))
    dp.add_handler(MessageHandler(Filters.photo, photo_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logger.info(f'start time: {datetime.now()}')
    NotetonUsersManager.init_instance()
    main()
