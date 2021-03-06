import sys
from datetime import datetime
from typing import List

from loguru import logger
from telegram import InlineQueryResultArticle, ParseMode, Update, \
    InlineQueryResultCachedPhoto, InputTextMessageContent, InlineQueryResult, \
    InlineQueryResultCachedSticker, \
    InlineQueryResultCachedGif, InlineQueryResultCachedAudio, \
    InlineQueryResultCachedDocument
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, \
    CallbackQueryHandler, MessageHandler, Filters, CallbackContext, \
    ChosenInlineResultHandler

from config import token, god_chat_id
from nt_list import NotetonList
from nt_list_item_file import NotetonListItemFile
from nt_state import NotetonState
from nt_user import NotetonUser

from nt_users_manager import NotetonUsersManager
from process_states import process_feedback, process_edit_list, \
    process_create_list, process_text_message_main_menu, \
    process_delete_list_state, process_create_list_state, \
    process_add_file_state, process_add_article_state, \
    process_edit_list_state
from telegram_buttons import generate_list_types_buttons, \
    generate_lists_buttons, generate_main_menu, generate_buttons_my_lists, \
    generate_button_with_one_list


def callback_query_handler(update: Update, context: CallbackContext):
    callback_query_id = update.callback_query.id
    chat_id = update.callback_query.message.chat_id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    text = update.callback_query.data
    logger.info(f'message in callback_query "{text}" from {user}')
    show_alert = False
    if user.get_state() == NotetonState.CREATE_LIST_TYPE:
        msg, result = process_create_list_state(text, user)
        if result:
            context.bot.delete_message(chat_id, user.lists_message_id)
    elif user.get_state() == NotetonState.ADD_FILE:
        msg, result = process_add_file_state(text, user)
        if result:
            context.bot.delete_message(chat_id, user.lists_message_id)
    elif user.get_state() == NotetonState.ADD_ARTICLE:
        msg, result = process_add_article_state(text, user)
        if result:
            context.bot.delete_message(chat_id, user.lists_message_id)
    else:
        if text.endswith(NotetonList.EDIT_COMMAND):
            msg = process_edit_list_state(text, user)
            show_alert = True
        elif text.endswith(NotetonList.DELETE_COMMAND):
            msg, result = process_delete_list_state(text, user)
            if result:
                nt_lists = NotetonUsersManager.get_lists_of_user(user.id)
                reply_markup = generate_buttons_my_lists(nt_lists)
                context.bot.edit_message_reply_markup(chat_id=chat_id,
                                                      message_id=user.lists_message_id,
                                                      reply_markup=reply_markup)

        else:
            msg = 'Unexpected command'

    context.bot.answer_callback_query(callback_query_id=callback_query_id,
                                      show_alert=show_alert,
                                      text=msg)


def inline_query(update: Update, context: CallbackContext):
    """Handle the inline query."""
    query = update.inline_query.query.lower()
    user = NotetonUsersManager.get_user(update.effective_user.id)
    if query.endswith(NotetonList.DELETE_ITEM_COMMAND):
        query = query[:query.index(NotetonList.DELETE_ITEM_COMMAND)]
    logger.info(f'inline query with query "{query}" from {user}')
    nt_lists = NotetonUsersManager.get_lists_of_user(user.id)
    nt_lists = list(filter(lambda x: x.list_name.startswith(query), nt_lists))
    if len(nt_lists) > 1:
        answer_items = []
        for nt_list in nt_lists:
            ans_text = InputTextMessageContent(nt_list.list_name)
            item_ = InlineQueryResultArticle(id=nt_list.id,
                                             title=nt_list.list_name,
                                             input_message_content=ans_text)
            answer_items.append(item_)
    elif len(nt_lists) == 1:
        nt_list = nt_lists[0]
        answer_items = get_list_items_by_type(nt_list, user)
        user.time_inline = datetime.now()
    else:
        ans_text = InputTextMessageContent(message_text='No lists')

        answer_items = [
            InlineQueryResultArticle(id='no_id',
                                     title='No lists with this name',
                                     input_message_content=ans_text,
                                     description='You have no lists with this '
                                                 'name, press "My lists" for '
                                                 'all lists')
        ]
    user.set_state(NotetonState.NO_ANSWER)
    update.inline_query.answer(answer_items, cache_time=5,
                               is_personal=True, timeout=300)


def get_list_items_by_type(nt_list: NotetonList,
                           user: NotetonUser) -> List[InlineQueryResult]:
    items = NotetonUsersManager.get_items_of_list(user.id, nt_list)
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
        elif nt_list.type == NotetonList.TYPE_AUDIO:
            item_ = InlineQueryResultCachedAudio(id=id_,
                                                 audio_file_id=item.file_id)
        elif nt_list.type == NotetonList.TYPE_DOCUMENT:
            item_ = InlineQueryResultCachedDocument(id=id_, title=item.title,
                                                    document_file_id=item.file_id)
        if item_:
            answer_items.append(item_)
    return answer_items


def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    logger.info(f'I have new text message: "{text}" from {user}')
    msg = None
    reply_markup = None
    last_inline_sec = 1e9
    need_update_message_id = False
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
        msg, need_update_message_id = process_create_list(text.lower(), user)
    elif user.get_state() == NotetonState.EDIT_LIST:
        msg, result = process_edit_list(text, user)
        if result:
            nt_lists = NotetonUsersManager.get_lists_of_user(user.id)
            reply_markup = generate_buttons_my_lists(nt_lists)
            context.bot.edit_message_reply_markup(chat_id=chat_id,
                                                  message_id=user.lists_message_id,
                                                  reply_markup=reply_markup)
            context.bot.delete_message(chat_id, update.message.message_id)
    elif user.get_state() == NotetonState.FEEDBACK:
        msg, feedback_msg = process_feedback(update.effective_user.username,
                                             update.effective_user.full_name,
                                             text,
                                             user)
        context.bot.send_message(chat_id=god_chat_id, text=feedback_msg)
    elif user.get_state() == NotetonState.MAIN_MENU:
        msg, reply_markup = process_text_message_main_menu(user, text)
        if reply_markup is not None:
            need_update_message_id = True

    if msg:
        sent_msg = context.bot.send_message(chat_id=chat_id,
                                            text=msg,
                                            reply_markup=reply_markup)
        if need_update_message_id:
            user.lists_message_id = sent_msg.message_id


def common_file_handler(user, bot, chat_id, file_id,
                        file_type, word, title=None):
    if user.get_state() == NotetonState.NO_ANSWER and \
            user.time_inline is not None and \
            (datetime.now() - user.time_inline).total_seconds() < \
            NotetonUsersManager.time_no_answer:
        user.set_state(NotetonState.MAIN_MENU)
        return None

    item = NotetonListItemFile(user_id=user.id,
                               file_id=file_id,
                               title=title)
    user.tmp_item = item
    lists = NotetonUsersManager.get_lists_of_user_by_type(user.id,
                                                          file_type)
    if not lists:
        bot.send_message(chat_id=chat_id,
                         text=f'Oops, you have no lists with {word},'
                              f'please, create at least one first')
    elif len(lists) == 1:
        msg, result = process_add_file_state(lists[0].list_name, user)
        reply_markup = generate_button_with_one_list(lists[0].list_name)
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=reply_markup)
        if result:
            user.set_state(NotetonState.MAIN_MENU)

    else:
        user.set_state(NotetonState.ADD_FILE)
        reply_markup = generate_lists_buttons(lists)

        msg = bot.send_message(chat_id=chat_id,
                               text=f'Choose the list:',
                               reply_markup=reply_markup)
        user.lists_message_id = msg.message_id


def photo_handler(update: Update, context: CallbackContext):

    photo_id = update.message.photo[-1].file_id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    logger.info(f'Photo handler from {user}')

    common_file_handler(user, context.bot, update.message.chat_id,
                        photo_id, NotetonList.TYPE_IMAGE, 'images')


def sticker_handler(update: Update, context: CallbackContext):
    sticker_id = update.message.sticker.file_id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    logger.info(f'Sticker handler from {user}')

    common_file_handler(user, context.bot, update.message.chat_id,
                        sticker_id, NotetonList.TYPE_STICKER, 'stickers')


def gif_handler(update: Update, context: CallbackContext):
    gif_id = update.message.animation.file_id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    logger.info(f'GIF handler from {user}')

    common_file_handler(user, context.bot, update.message.chat_id,
                        gif_id, NotetonList.TYPE_GIF, 'gifs')


def audio_handler(update: Update, context: CallbackContext):
    audio_id = update.message.audio.file_id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    logger.info(f'Audio handler from {user}')

    common_file_handler(user, context.bot, update.message.chat_id,
                        audio_id, NotetonList.TYPE_AUDIO, 'audios')


def document_handler(update: Update, context: CallbackContext):
    document_id = update.message.document.file_id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    logger.info(f'Document handler from user {user}')

    common_file_handler(user, context.bot, update.message.chat_id,
                        document_id, NotetonList.TYPE_DOCUMENT, 'documents',
                        update.message.document.file_name)


def test_handler(update: Update, context: CallbackContext):
    logger.info(f'Test handler')


def start(update: Update, context: CallbackContext):

    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id,
                                        update.effective_user.username,
                                        update.effective_user.full_name)
    logger.info(f'I have start command from {user}')

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

    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    logger.info(f'I have create_list command from {user}')

    user.set_state(NotetonState.CREATE_LIST_NAME)
    context.bot.send_message(chat_id=chat_id,
                             text='Send me name of list (less than 20 symbols,'
                                  ' letters, numbers and underscore _)')


def my_lists(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    logger.info(f'I have my_lists command from {user}')

    nt_lists = NotetonUsersManager.get_lists_of_user(user.id)
    reply_markup = generate_buttons_my_lists(nt_lists)

    msg = context.bot.send_message(chat_id=chat_id,
                                   text=f'Your lists:\n'
                                        f'✏ - edit list name\n'
                                        f'❌ - delete',
                                   reply_markup=reply_markup)
    user.lists_message_id = msg.message_id


def info_and_help(update: Update, context: CallbackContext):

    chat_id = update.message.chat_id
    user = NotetonUsersManager.get_user(update.effective_user.id)
    logger.info(f'I have info_and_help command from {user}')

    context.bot.send_message(chat_id=chat_id,
                             text=f'I have command info_and_help')


def feedback(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = NotetonUsersManager.get_user(user_id)
    logger.info(f'I have feedback command from {user}')
    user.set_state(NotetonState.FEEDBACK)
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id,
                             text=f'Send me feedback message:')


def get_stat(update: Update, context: CallbackContext):
    user = NotetonUsersManager.get_user(update.effective_user.id)
    logger.info(f'get_stat command form  {user}')
    if str(update.message.chat_id) == god_chat_id:
        users = NotetonUsersManager.get_users()
        context.bot.send_message(chat_id=god_chat_id,
                                 text=f'We have {len(users)} users')
        msg = f'last users\n' + '\n'.join(map(str, users[:10]))
        context.bot.send_message(chat_id=god_chat_id,
                                 text=msg)


def chosen_inline_result_handler(update: Update, context: CallbackContext):
    query = update.chosen_inline_result.query
    if query.endswith(NotetonList.DELETE_ITEM_COMMAND):
        user = NotetonUsersManager.get_user(update.effective_user.id)
        list_name = query[:query.index(NotetonList.DELETE_ITEM_COMMAND)]
        logger.info(f'chosen_inline_result_handler query {query} from {user}')
        nt_list = NotetonUsersManager.get_list_of_user_by_name(user.id,
                                                               list_name)
        item_id = update.chosen_inline_result.result_id
        NotetonUsersManager.delete_list_item(nt_list.id, item_id)

        logger.debug(f'chosen inline, user {user.id}')
        user.set_state(NotetonState.MAIN_MENU)


@logger.catch
def main():
    config = {
        'handlers': [
            {'sink': sys.stdout, 'level': 'INFO'},
            {'sink': 'logs/logs.log', 'serialize': False, 'level': 'DEBUG'},
        ],
    }
    logger.configure(**config)
    logger.info('Bot has started')
    NotetonUsersManager.init_instance()

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    updater.logger = logger
    dp.logger = logger
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("create_list", create_list))
    dp.add_handler(CommandHandler("my_lists", my_lists))
    dp.add_handler(CommandHandler("info_and_help", info_and_help))
    dp.add_handler(CommandHandler("send_feedback", feedback))
    dp.add_handler(CommandHandler("stat", get_stat))
    dp.add_handler(CommandHandler("help", info_and_help))

    dp.add_handler(InlineQueryHandler(inline_query))
    dp.add_handler(ChosenInlineResultHandler(chosen_inline_result_handler))
    dp.add_handler(CallbackQueryHandler(callback_query_handler))

    dp.add_handler(MessageHandler(Filters.text, message_handler))
    dp.add_handler(MessageHandler(Filters.photo, photo_handler))
    dp.add_handler(MessageHandler(Filters.sticker, sticker_handler))
    dp.add_handler(MessageHandler(Filters.animation, gif_handler))
    dp.add_handler(MessageHandler(Filters.audio, audio_handler))
    dp.add_handler(MessageHandler(Filters.document, document_handler))
    dp.add_handler(MessageHandler(Filters.all, test_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
