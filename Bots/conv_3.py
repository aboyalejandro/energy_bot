#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import pandas as pd
import requests
import numpy as np
from bs4 import BeautifulSoup
import datetime
from datetime import date

import logging
from typing import Dict

from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ['Washing machine', 'Oven'],
    ['Size of house', 'Heater'],
    ['Done'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f'{key} - {value}' for key, value in user_data.items()]
    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""
    update.message.reply_text(
        "Hi! My name is Energy \U0001F4A1 Bot \U0001F916. I will ask you a few questions.\n\n"
        #"I have listed the most important appliances for a house."
        "\U0001F449 Please pick the appliances in your home and add the power consumption of these appliances in Watts.\n\n"
        "\U0001F449 In addition to that please add the size of your house/appartment in square meters (sq m)\n\n"
        "After you answer these questions I will optimize \U0001F4B9 your energy consumption and give you "
        "suggestions on when you should use these appliances.",
        reply_markup=markup,
    )

    return CHOOSING


def regular_choice(update: Update, context: CallbackContext) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(f'Your {text.lower()}? Tell me the power in Watts.')

    return TYPING_REPLY


def custom_choice(update: Update, context: CallbackContext) -> int:
    """Ask the user for the size of house."""
    update.message.reply_text(
        'Alright, please tell me the size of your house in square meters! (e.g. 50)"'
    )
    text = update.message.text
    context.user_data['choice'] = text

    return TYPING_REPLY


def received_information(update: Update, context: CallbackContext) -> int:
    """Store info provided by user and ask for the next category."""
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text(
        "Neat! Just so you know, this is what you already told me:"
        f"{facts_to_str(user_data)}You can tell me more, or change your opinion"
        " on something.",
        reply_markup=markup,
    )

    return CHOOSING


def done(update: Update, context: CallbackContext) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(
        f"I learned these facts about your house: {facts_to_str(user_data)}Until next time!",
        reply_markup=ReplyKeyboardRemove(),
    )

    today = date.today().strftime('%d-%m-%Y')

    url = 'https://tarifaluzhora.es/'

    headers= {'Accept-Encoding':'gzip, deflate',
              'Accept-Language':'en-US,en;q=0.9',
              'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'}

    response = requests.get(url, headers = headers)
    response.status_code

    soup = BeautifulSoup(response.content)
    #print(soup.prettify())

    average_today_price = soup.find('div',attrs={'class':'inner_block gauge_day'})
    average_today_price = average_today_price.span.string[:6]

    cheapest_today_time = soup.find('div',attrs={'class':'inner_block gauge_low'})
    cheapest_today_time = cheapest_today_time.span.string.replace('h','')

    expensive_today_time = soup.find('div',attrs={'class':'inner_block gauge_hight'})
    expensive_today_time = expensive_today_time.span.string.replace('h','')

    lowest_today_price = soup.find('span',attrs={'class':'sub_text green'})
    lowest_today_price= lowest_today_price.get_text().replace('\t','').replace('\n','')[:7]

    highest_today_price = soup.find('span',attrs={'class':'sub_text red'})
    highest_today_price= highest_today_price.get_text().replace('\t','').replace('\n','')[:7]

    update.message.reply_text(f'Today is {today}')
    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'Average price of today is: {average_today_price}€ per kwh')
    update.message.reply_text(f'Lowest price of today is: {lowest_today_price}€ per kwh')
    update.message.reply_text(f'Highest price of today is: {highest_today_price}€ per kwh')
    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'Cheapest time of today was between {cheapest_today_time} hs')
    update.message.reply_text(f'Expensive time of today was between {expensive_today_time} hs')

    hour_range = soup.find_all('span',attrs={'itemprop':'description'})
    hour_price = soup.find_all('span',attrs={'itemprop':'price'})

    hours = []

    for i in hour_range:
        hours.append(i.string.replace(':','').replace('h',''))

    prices = []

    for i in hour_price:
        prices.append(i.string.replace('€/kW','').replace('h','').strip())

    price_per_hour = pd.DataFrame()
    price_per_hour['Hours'] = hours
    price_per_hour['Prices'] = prices
    price_per_hour['Prices'] = price_per_hour['Prices'].astype(float)
    price_per_hour['Avg Today'] = price_per_hour['Prices'].mean()
    price_per_hour['Deviation'] = price_per_hour['Prices'].mean() - price_per_hour['Prices']

    def price_flag(x):
        if x<0:
            return 'Expensive'
        elif x>0:
            return 'Cheaper'
        else:
            return 'Regular'

    price_per_hour['Price Flag'] = price_per_hour['Deviation'].apply(price_flag)
    update.message.reply_text(price_per_hour)


    return ConversationHandler.END, update.message.user_data


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("5374346481:AAFjRjPVVVVdyqatr0f1wFaPQphcRaEsOrc")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex('^(Washing machine|Oven|Heater)$'), regular_choice
                ),
                MessageHandler(Filters.regex('^Size of house$'), custom_choice),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
