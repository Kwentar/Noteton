import logging
from datetime import datetime

from telegram import InlineQueryResultArticle, ParseMode, Update, \
    InlineQueryResultCachedPhoto, Bot
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, \
    CallbackQueryHandler, MessageHandler, Filters, CallbackContext

from config import token, god_chat_id
from nt_list import NotetonList
from nt_list_item_photo import NotetonListItemPhoto
from nt_state import NotetonState
from nt_user import NotetonUser

from nt_users_manager import NotetonUsersManager
from telegram_buttons import generate_list_types_buttons, \
    generate_lists_buttons, generate_main_menu, generate_buttons_my_lists

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger('NOTETON MAIN')


def callback_query_handler(update: Update, context: CallbackContext):
    callback_query_id = update.callback_query.id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    text = update.callback_query.data
    logger.info(f'message in callback_query {text}')
    show_alert = False
    if user.get_state() == NotetonState.CREATE_LIST_TYPE:
        msg = process_create_list_state(text, user)
    elif user.get_state() == NotetonState.ADD_PHOTO:
        msg = process_add_photo_state(text, user)
    else:
        if text.endswith(NotetonList.EDIT_COMMAND):
            msg = process_edit_list_state(text, user)
            show_alert = True
        elif text.endswith(NotetonList.DELETE_COMMAND):
            msg = process_delete_list_state(text, user)
        else:
            msg = 'Unexpected command'

    context.bot.answer_callback_query(callback_query_id=callback_query_id,
                                      show_alert=show_alert,
                                      text=msg)


def process_delete_list_state(text: str, user: NotetonUser):
    list_name = text[:len(text) - len(NotetonList.DELETE_COMMAND)]
    user.tmp_list = NotetonUsersManager.get_list_of_user_by_name(user.user_id,
                                                                 list_name)
    if user.tmp_list is None:
        logger.error(f'list {list_name} of user {user.user_id} not '
                     f'found in process_delete_list_command')
        return f'I guess you are trying to delete nonexistent list 🤔'
    else:
        user.set_state(NotetonState.MAIN_MENU)
        res = NotetonUsersManager.delete_list(user.user_id, user.tmp_list)
        if res['ResponseMetadata']['HTTPStatusCode'] == 200:
            return f'list {list_name} has been deleted'
        else:
            logger.warning(f'Problem with deleting {list_name} of user '
                           f'{user.user_id}, resp code is '
                           f'{res["ResponseMetadata"]["HTTPStatusCode"]}')
            return f'Something bad happened, we will check it!'


def process_edit_list_state(text: str, user: NotetonUser):
    list_name = text[:len(text) - len(NotetonList.EDIT_COMMAND)]
    user.tmp_list = NotetonUsersManager.get_list_of_user_by_name(user.user_id,
                                                                 list_name)
    user.set_state(NotetonState.EDIT_LIST)
    return f'Send me new name for list {list_name}'


def process_add_photo_state(text: str, user: NotetonUser):
    lists = NotetonUsersManager.get_lists_of_user(user.user_id)
    if text in [x.list_name for x in lists]:
        list_ = NotetonUsersManager.get_list_of_user_by_name(user.user_id, text)
        user.tmp_item.list_id = list_.id
        user.tmp_item.generate_key()
        NotetonUsersManager.add_photo_to_list(user.tmp_item)
        user.set_state(NotetonState.MAIN_MENU)
        return f'Images added to list {text}, you can get whole list via ' \
               f'@noteton_bot {text}'

    else:
        return f'Wrong list, please, use buttons'


def process_create_list_state(text: str, user: NotetonUser):
    types = NotetonList.get_types()
    if text in types:
        user.tmp_list.type = text
        NotetonUsersManager.add_list_to_user(user.user_id, user.tmp_list)
        user.set_state(NotetonState.MAIN_MENU)
        return f'I created new list for you: {user.tmp_list.list_name}'
    else:
        return 'Wrong type, please, use buttons'


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
                item = InlineQueryResultCachedPhoto(id=id_,
                                                    photo_file_id=item.file_id)
                answer_items.append(item)
        update.inline_query.answer(answer_items, cache_time=5, is_personal=True,
                                   timeout=300)


def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    logger.info(f'I have new message: {text} from {user_id}')
    msg = None
    reply_markup = None

    if text == 'Main menu':
        start(update, context)
    elif text == 'Create list':
        create_list(update, context)
    elif text == 'My lists':
        my_lists(update, context)
    elif text == 'Info & Help':
        info_and_help(update, context)
    elif text == 'Send feedback':
        feedback(update, context)
    elif user.get_state() == NotetonState.CREATE_LIST_NAME:
        reply_markup = generate_list_types_buttons()
        msg = process_create_list(chat_id, context, text, user)
    elif user.get_state() == NotetonState.EDIT_LIST:
        msg = process_edit_list(text, user)
    elif user.get_state() == NotetonState.FEEDBACK:
        msg = process_feedback(update.effective_user.username,
                               update.effective_user.full_name,
                               text,
                               context.bot,
                               user)
    if msg:
        context.bot.send_message(chat_id=chat_id,
                                 text=msg,
                                 reply_markup=reply_markup)


def process_feedback(username: str,
                     full_name: str,
                     text: str,
                     bot: Bot,
                     user: NotetonUser):
    """
    Process feedback command
    :param username: user username from telegram
    :param full_name: user full name from telegram
    :param text: feedback message
    :param bot: telegram.Bot for sending message
    :param user: current user
    :return: Answer to user, change user state to MAIN_MENU
    """
    feedback_text = f'******FEEDBACK*******\n' \
                    f'from user {user.user_id} with username ' \
                    f'{username} and fullname ' \
                    f'{full_name}:\n{text}'
    bot.send_message(chat_id=god_chat_id, text=feedback_text)
    user.set_state(NotetonState.MAIN_MENU)
    return 'Message has been sent, thank you!'


def process_edit_list(new_list_name: str,
                      user: NotetonUser):
    """
    Process editing list, currently only name can be changed
    :param new_list_name: new list name
    :param user: current user
    :return: message will be send to user, change user state to MAIN_MENU
    """
    nt_lists = NotetonUsersManager.get_lists_of_user(user.user_id)
    names = [x.list_name for x in nt_lists]
    val_result, msg = NotetonList.validate_list_name(new_list_name, names)
    if val_result:
        user.set_state(NotetonState.MAIN_MENU)
        user.tmp_list.list_name = new_list_name
        NotetonUsersManager.change_list_name(user.user_id,
                                             user.tmp_list)

        msg = f'The list name has been changed ✅'
    return msg


def process_create_list(chat_id, context, list_name, user):
    """
    Process create list logic
    :param chat_id: chat id for answer
    :param context: context from telegram api
    :param list_name: list name
    :param user: current user
    :return: None, change user state to CREATE_LIST_TYPE and send invite
             to choosing list type
    """
    nt_lists = NotetonUsersManager.get_lists_of_user(user.user_id)
    names = [x.list_name for x in nt_lists]
    val_result, msg = NotetonList.validate_list_name(list_name, names)
    if val_result:
        user.tmp_list = NotetonList(user.user_id, list_name)
        user.set_state(NotetonState.CREATE_LIST_TYPE)
        msg = 'Choose the type of list:'
    return msg


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
    user.set_state(NotetonState.ADD_PHOTO)
    lists = NotetonUsersManager.get_lists_of_user_by_type(user_id,
                                                          NotetonList.TYPE_IMAGES)
    if not lists:
        context.bot.send_message(chat_id=chat_id,
                                 text=f'Oops, you have no lists with images,'
                                      f'please, create at least one first')
        return
    reply_markup = generate_lists_buttons(lists)

    context.bot.send_message(chat_id=chat_id,
                             text=f'Choose the list:',
                             reply_markup=reply_markup)


def start(update: Update, context: CallbackContext):
    logger.info(f'I have start command')

    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)

    user.set_state(NotetonState.MAIN_MENU)
    reply_markup = generate_main_menu()
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
    user = NotetonUsersManager.get_user(update.effective_user.id)
    nt_lists = NotetonUsersManager.get_lists_of_user(user.user_id)
    reply_markup = generate_buttons_my_lists(nt_lists)

    msg = context.bot.send_message(chat_id=chat_id,
                                   text=f'Your lists:',
                                   reply_markup=reply_markup)
    user.lists_message_id = msg.message_id


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
                             text=f'Send me feedback message:')


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
