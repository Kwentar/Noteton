import logging
from datetime import datetime
from uuid import uuid4

from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, \
    CallbackQueryHandler, MessageHandler, Filters, CallbackContext

from config import token
from nt_state import NotetonState

import boto3

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger('NOTETON MAIN')


def build_menu(buttons, n_cols=1, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    return menu


def read_file(file_name, line_converter):
    with open(file_name, 'r', encoding='utf8') as f:
        lines = f.readlines()[1:]
    lines = [line.strip() for line in lines if line]
    items = list(map(line_converter, lines))

    return items


def get_description(description_file):
    with open(description_file, 'r', encoding='utf8') as f:
        text = f.readlines()[0].strip()
    return text


def telegram_menu(bot, update):
    telegram_user = update.message.chat_id

    button_list = [
        [InlineKeyboardButton("Меню",
                              switch_inline_query_current_chat='menu')],
        [InlineKeyboardButton("Акции",
                              switch_inline_query_current_chat='events')],
        [InlineKeyboardButton("О кофейне",
                              callback_data='about')],
    ]
    reply_markup = InlineKeyboardMarkup(button_list)

    bot.send_message(chat_id=telegram_user, text='Выберите:',
                     reply_markup=reply_markup)


def callback_query_handler(bot, update):
    print(update)
    cqd = update.callback_query.data
    chat_id = update.callback_query.message.chat_id



def inline_query(update, context):
    """Handle the inline query."""
    query = context.inline_query.query

    context.inline_query.answer('results', cache_time=10)


def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    logger.info(f'I have new message: {text}')

    if NotetonState.get_state() == NotetonState.MAIN_MENU:
        if text == 'Create list':
            create_list(update, context)
        elif text == 'My lists':
            my_lists(update, context)
        elif text == 'Info & Help':
            info_and_help(update, context)
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id,
                             text=f'I have new message: {text}')


def start(update: Update, context: CallbackContext):
    logger.info(f'I have start command')

    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    NotetonState.change_state(NotetonState.MAIN_MENU)
    buttons = [['Create list'], ['My lists'], ['Info & Help']]

    reply_markup = ReplyKeyboardMarkup(buttons)

    context.bot.send_message(chat_id=chat_id,
                             text='Main menu:\n'
                                  '/create_list \n'
                                  '/my_lists\n'
                                  '/info_and_help',
                             reply_markup=reply_markup)


def create_list(update: Update, context: CallbackContext):
    logger.info(f'I have create_list command')

    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id,
                             text=f'I have command create_list')


def my_lists(update: Update, context: CallbackContext):
    logger.info(f'I have my_lists command')

    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id,
                             text=f'I have command my_list')


def info_and_help(update: Update, context: CallbackContext):
    logger.info(f'I have info_and_help command')

    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id,
                             text=f'I have command info_and_help')


def main():
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("create_list", create_list))
    dp.add_handler(CommandHandler("my_lists", my_lists))
    dp.add_handler(CommandHandler("info_and_help", info_and_help))
    dp.add_handler(CommandHandler("help", info_and_help))

    dp.add_handler(InlineQueryHandler(inline_query))
    dp.add_handler(CallbackQueryHandler(callback_query_handler))
    dp.add_handler(MessageHandler(Filters.text, message_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logger.info(f'start time: {datetime.now()}')
    main()
