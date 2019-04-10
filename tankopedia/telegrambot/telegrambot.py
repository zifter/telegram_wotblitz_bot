# coding=utf8
import random

from wg import WOTBTankopedia, WOTBAccounts
from telegram.ext import Updater, CommandHandler, MessageHandler, InlineQueryHandler, Filters
from telegram import ParseMode, InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from config import TELEGRAM_TOKEN
from telegrambot.constants import *
from telegrambot.renderer import render_player, render_vehicle

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s: %(name)s: %(levelname)s: %(message)s')
g_logger = logging.getLogger()
g_logger.setLevel(logging.DEBUG)

g_current_keyboard = {}
tankopedia = WOTBTankopedia()
accounts = WOTBAccounts()


def start(bot, update):
    msg = random.choice(HELLO).format(update.message.from_user.first_name)
    update.message.reply_text(msg)


def help(bot, update):
    msg = random.choice(HELP)
    update.message.reply_text(msg)


def on_request_failed(bot, update):
    reply_markup = None
    if update.message.chat_id in g_current_keyboard:
        g_current_keyboard.pop(update.message.chat_id)
        reply_markup = ReplyKeyboardRemove()

    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(CANT_FIND), reply_markup=reply_markup)


def on_one_vehicle_found(bot, update, vehicle):
    msg = render_vehicle(vehicle)

    reply_markup = None
    if update.message.chat_id in g_current_keyboard:
        g_current_keyboard.pop(update.message.chat_id)
        reply_markup = ReplyKeyboardRemove()

    bot.sendMessage(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def on_many_vehicles_found(bot, update, vehicles):
    custom_keyboard = [[v.get_loc_name() for v in vehicles]]

    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=random.choice(CANT_DETECT_VEHICLE),
                    reply_markup=reply_markup)

    g_current_keyboard[update.message.chat_id] = True


def on_one_account_found(bot, update, account):
    reply_markup = None
    if update.message.chat_id in g_current_keyboard:
        g_current_keyboard.pop(update.message.chat_id)
        reply_markup = ReplyKeyboardRemove()

    detailed_account = accounts.get_player_info_for(account.account_id)
    msg = render_player(detailed_account)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def on_many_accounts_found(bot, update, accounts):
    custom_keyboard = [[v.nickname for v in accounts]]

    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=random.choice(CANT_DETECT_ACCOUNT),
                    reply_markup=reply_markup)

    g_current_keyboard[update.message.chat_id] = True


def on_message(bot, update):
    choices = tankopedia.fuzzy_search_vehicle(update.message.text)
    if len(choices) == 1:
        on_one_vehicle_found(bot, update, choices[0])
    elif len(choices) > 1:
        on_many_vehicles_found(bot, update, choices)
    else:
        choices = accounts.fuzzy_search(update.message.text)[0:10]
        if len(choices) == 1:
            on_one_account_found(bot, update, choices[0])
        elif len(choices) > 1:
            on_many_accounts_found(bot, update, choices)
        else:
            on_request_failed(bot, update)


def inline_search(bot, update):
    query = update.inline_query.query
    if not query or len(query) < 2:
        return

    results = list()
    choices = tankopedia.fuzzy_search_vehicle(query)
    for choice in choices:
        results.append(
            InlineQueryResultArticle(
                id=choice.uuid,
                title=choice.get_loc_name(),
                thumb_url=choice.image_preview,
                thumb_width=200,
                thumb_height=200,
                input_message_content=InputTextMessageContent(render_vehicle(choice), parse_mode=ParseMode.HTML)
            )
        )
    accounts_list = accounts.fuzzy_search_and_get_info(query)
    for account in accounts_list:
        results.append(
            InlineQueryResultArticle(
                id=account.raw.account_id,
                title=account.raw.nickname,
                input_message_content=InputTextMessageContent(render_player(account), parse_mode=ParseMode.HTML)
            )
        )

    bot.answerInlineQuery(update.inline_query.id, results)


def run():
    g_logger.info('Start bot...')
    updater = Updater(TELEGRAM_TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, on_message))
    updater.dispatcher.add_handler(InlineQueryHandler(inline_search))

    updater.start_polling()
    updater.idle()

    g_logger.info('Bot finished')


if __name__ == '__main__':
    run()
