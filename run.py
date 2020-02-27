import logging
from datetime import datetime
from typing import List

from telegram import InlineQueryResultArticle, ParseMode, Update, \
    InlineQueryResultCachedPhoto, InputTextMessageContent, InlineQueryResult, InlineQueryResultCachedSticker, \
    InlineQueryResultCachedGif
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, \
    CallbackQueryHandler, MessageHandler, Filters, CallbackContext, \
    ChosenInlineResultHandler

from config import token, god_chat_id
from nt_list import NotetonList
from nt_list_item_article import NotetonListItemArticle
from nt_list_item_file import NotetonListItemFile
from nt_state import NotetonState
from nt_user import NotetonUser

from nt_users_manager import NotetonUsersManager
from process_states import process_feedback, process_edit_list, process_create_list, process_text_message_main_menu, \
    process_delete_list_state, process_create_list_state, process_add_file_state, process_add_article_state, \
    process_edit_list_state
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
    elif user.get_state() == NotetonState.ADD_FILE:
        msg = process_add_file_state(text, user)
    elif user.get_state() == NotetonState.ADD_ARTICLE:
        msg = process_add_article_state(text, user)
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


def inline_query(update: Update, context: CallbackContext):
    """Handle the inline query."""
    query = update.inline_query.query
    user = NotetonUsersManager.get_user(update.effective_user.id)
    nt_list = NotetonUsersManager.get_list_of_user_by_name(user.user_id, query)
    if nt_list:
        answer_items = get_list_items_by_type(nt_list, user)
        user.set_state(NotetonState.NO_ANSWER)
        user.time_inline = datetime.now()
        update.inline_query.answer(answer_items, cache_time=5, is_personal=True,
                                   timeout=300)


def get_list_items_by_type(nt_list: NotetonList,
                           user: NotetonUser) -> List[InlineQueryResult]:
    items = NotetonUsersManager.get_items_of_list(user.user_id, nt_list)
    answer_items = []
    for item in items:
        id_ = item.id
        item_ = None
        if nt_list.type == NotetonList.TYPE_ARTICLE:
            ans_text = InputTextMessageContent(item.text)
            item_ = InlineQueryResultArticle(id=id_,
                                             title=item.text,
                                             input_message_content=ans_text)
        elif nt_list.type == NotetonList.TYPE_IMAGE:
            item_ = InlineQueryResultCachedPhoto(id=id_,
                                                 photo_file_id=item.file_id)
        elif nt_list.type == NotetonList.TYPE_STICKER:
            item_ = InlineQueryResultCachedSticker(id=id_,
                                                   sticker_file_id=item.file_id)
        elif nt_list.type == NotetonList.TYPE_GIF:
            item_ = InlineQueryResultCachedGif(id=id_,
                                               gif_file_id=item.file_id)
        if item_:
            answer_items.append(item_)
    return answer_items


def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    logger.info(f'I have new message: {text} from {user_id}')
    msg = None
    reply_markup = None
    last_inline_sec = 1e9
    if user.time_inline is not None:
        last_inline_sec = (datetime.now() - user.time_inline).total_seconds()
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
    elif user.get_state() == NotetonState.NO_ANSWER and \
            last_inline_sec > NotetonUsersManager.time_no_answer:
        user.set_state(NotetonState.MAIN_MENU)
    elif user.get_state() == NotetonState.CREATE_LIST_NAME:
        reply_markup = generate_list_types_buttons()
        msg = process_create_list(text, user)
    elif user.get_state() == NotetonState.EDIT_LIST:
        msg = process_edit_list(text, user)
    elif user.get_state() == NotetonState.FEEDBACK:
        msg, feedback_msg = process_feedback(update.effective_user.username,
                                             update.effective_user.full_name,
                                             text,
                                             user)
        context.bot.send_message(chat_id=god_chat_id, text=feedback_msg)
    elif user.get_state() == NotetonState.MAIN_MENU:
        msg, reply_markup = process_text_message_main_menu(user, text)

    if msg:
        context.bot.send_message(chat_id=chat_id,
                                 text=msg,
                                 reply_markup=reply_markup)


def photo_handler(update: Update, context: CallbackContext):
    photo_id = update.message.photo[-1].file_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    if user.time_inline:
        logger.debug(f'photo handler, time is {datetime.now()}, total seconds is'
                     f'{(datetime.now() - user.time_inline).total_seconds()}')
    if user.get_state() == NotetonState.NO_ANSWER and \
            user.time_inline is not None and \
            (datetime.now() - user.time_inline).total_seconds() < \
            NotetonUsersManager.time_no_answer:
        user.set_state(NotetonState.MAIN_MENU)
        return

    chat_id = update.message.chat_id
    item = NotetonListItemFile(user_id=user_id,
                               file_id=photo_id)
    user.tmp_item = item
    user.set_state(NotetonState.ADD_FILE)
    lists = NotetonUsersManager.get_lists_of_user_by_type(user_id,
                                                          NotetonList.TYPE_IMAGE)
    if not lists:
        context.bot.send_message(chat_id=chat_id,
                                 text=f'Oops, you have no lists with images,'
                                      f'please, create at least one first')
        return
    reply_markup = generate_lists_buttons(lists)

    context.bot.send_message(chat_id=chat_id,
                             text=f'Choose the list:',
                             reply_markup=reply_markup)


def sticker_handler(update: Update, context: CallbackContext):
    logger.info(f'Sticker handler')
    sticker_id = update.message.sticker.file_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    if user.get_state() == NotetonState.NO_ANSWER and \
            user.time_inline is not None and \
            (datetime.now() - user.time_inline).total_seconds() < \
            NotetonUsersManager.time_no_answer:
        user.set_state(NotetonState.MAIN_MENU)
        return

    chat_id = update.message.chat_id
    item = NotetonListItemFile(user_id=user_id,
                               file_id=sticker_id)
    user.tmp_item = item
    user.set_state(NotetonState.ADD_FILE)
    lists = NotetonUsersManager.get_lists_of_user_by_type(user_id,
                                                          NotetonList.TYPE_STICKER)
    if not lists:
        context.bot.send_message(chat_id=chat_id,
                                 text=f'Oops, you have no lists with stickers,'
                                      f'please, create at least one first')
        return
    reply_markup = generate_lists_buttons(lists)

    context.bot.send_message(chat_id=chat_id,
                             text=f'Choose the list:',
                             reply_markup=reply_markup)


def gif_handler(update: Update, context: CallbackContext):
    logger.info(f'GIF handler')
    gif_id = update.message.animation.file_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    if user.get_state() == NotetonState.NO_ANSWER and \
            user.time_inline is not None and \
            (datetime.now() - user.time_inline).total_seconds() < \
            NotetonUsersManager.time_no_answer:
        user.set_state(NotetonState.MAIN_MENU)
        return

    chat_id = update.message.chat_id
    item = NotetonListItemFile(user_id=user_id,
                               file_id=gif_id)
    user.tmp_item = item
    user.set_state(NotetonState.ADD_FILE)
    lists = NotetonUsersManager.get_lists_of_user_by_type(user_id,
                                                          NotetonList.TYPE_GIF)
    if not lists:
        context.bot.send_message(chat_id=chat_id,
                                 text=f'Oops, you have no lists with gifs,'
                                      f'please, create at least one first')
        return
    reply_markup = generate_lists_buttons(lists)

    context.bot.send_message(chat_id=chat_id,
                             text=f'Choose the list:',
                             reply_markup=reply_markup)


def test_handler(update: Update, context: CallbackContext):
    logger.info(f'Sticker handler')


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


def chosen_inline_result_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    # user.set_state(NotetonState.NO_ANSWER)
    # user.time_inline = datetime.now()
    logger.debug(f'chosen inline, user {user.user_id}')


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
    dp.add_handler(ChosenInlineResultHandler(chosen_inline_result_handler))
    dp.add_handler(CallbackQueryHandler(callback_query_handler))
    dp.add_handler(MessageHandler(Filters.text, message_handler))
    dp.add_handler(MessageHandler(Filters.photo, photo_handler))
    dp.add_handler(MessageHandler(Filters.sticker, sticker_handler))
    dp.add_handler(MessageHandler(Filters.animation, gif_handler))
    dp.add_handler(MessageHandler(Filters.all, test_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logger.info(f'start time: {datetime.now()}')
    NotetonUsersManager.init_instance()
    main()
