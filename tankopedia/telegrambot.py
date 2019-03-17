#coding=utf8
import random
import logging

import wg
from telegram.ext import Updater, CommandHandler, MessageHandler, InlineQueryHandler, Filters
from telegram import ParseMode, InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup, ReplyKeyboardHide
from config import TELEGRAM_TOKEN


import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s: %(name)s: %(levelname)s: %(message)s')
g_logger = logging.getLogger()
g_logger.setLevel(logging.DEBUG)

HELLO = [
    u'Привет, {}! Я бот танкопедии WOT Blitz!',
    u'Здарова, {}! Я знаю все про танки из WOT Blitz!',
]

HELP = [
    u'Я бот танкопедии WOT Blitz! Напиши мне имя танка, и я покажу тебе информацию о нем! Например:'
]

CANT_DETECT = [
    u'Таакс, что-то не совсем понял, какой ты танк хочешь, давай выберем?',
    u'Выбери, какой конкретно танк ты имеешь ввиду.'
]

CANT_FIND = [
    u'Я не понимать :( Попробуй уточнить имя танка.',
    u'Уточни, какой танк ты хочешь. Попробуй уточнить имя танка.'
]

g_current_keyboard = {}

def format_vehicle_message(vehicle):
    msg_pattern = u"""
<a href=\'%(tankopedia)s\'>%(name)s (%(nation)s)</a>
%(prem)s%(type)s %(level)s уровня
Цена: %(cost)s
<i>%(descr)s</i>
<a href=\'%(image_url)s\'>&#160;</a>
    """
    context = {
        'tankopedia': vehicle.tankopedia_url,
        'name': vehicle.get_loc_name(),
        'nation': vehicle.get_loc_nation(),
        'image_url': vehicle.image_normal,
        'descr': vehicle.description,
        'cost': vehicle.get_loc_cost(),
        'prem': u'Премиум ' if vehicle.is_premium else u'',
        'level': vehicle.tier,
        'type': vehicle.get_loc_type(),
    }

    msg = msg_pattern % context
    return msg

def start(bot, update):
    msg = random.choice(HELLO).format(update.message.from_user.first_name)
    update.message.reply_text(msg)

def help(bot, update):
    msg = random.choice(HELP)
    update.message.reply_text(msg)

def on_vehicle_not_found(bot, update):
    reply_markup = None
    if update.message.chat_id in g_current_keyboard:
        g_current_keyboard.pop(update.message.chat_id)
        reply_markup = ReplyKeyboardHide()

    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(CANT_FIND), reply_markup=reply_markup)


def on_one_vehicle_found(bot, update, vehicle):
    msg = format_vehicle_message(vehicle)

    reply_markup = None
    if update.message.chat_id in g_current_keyboard:
        g_current_keyboard.pop(update.message.chat_id)
        reply_markup = ReplyKeyboardHide()

    bot.sendMessage(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def on_many_vehicles_found(bot, update, vehicles):
    custom_keyboard = [[v.get_loc_name() for v in vehicles]]

    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=random.choice(CANT_DETECT),
                    reply_markup=reply_markup)

    g_current_keyboard[update.message.chat_id] = True


def on_message(bot, update):
    choices = wg.get_choices_for_request(update.message.text)
    if len(choices) == 0:
        on_vehicle_not_found(bot, update)
    elif len(choices) == 1:
        on_one_vehicle_found(bot, update, choices[0])
    else:
        on_many_vehicles_found(bot, update, choices)


def inline_search(bot, update):
    query = update.inline_query.query
    if not query or len(query) < 2:
        return
    results = list()
    choices = reversed(wg.get_choices_for_request(query))
    for choice in choices:
        results.append(
            InlineQueryResultArticle(
                id=choice.uuid,
                title=choice.get_loc_name(),
                thumb_url=choice.image_preview,
                thumb_width=200,
                thumb_height=200,
                input_message_content=InputTextMessageContent(format_vehicle_message(choice), parse_mode=ParseMode.HTML)
                 )
        )
    bot.answerInlineQuery(update.inline_query.id, results)


def run():
    wg.get_all_data()
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