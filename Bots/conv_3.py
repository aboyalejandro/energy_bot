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
import telebot
#import scraping_stuff

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





# ---------------------------------------------------------------------------------
# This is where the bot starts
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
    user_data_test = context.user_data
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

    #update.message.reply_text(f'Today is {today}')
    #update.message.reply_text('----------------------------------------------------------------------')
    #update.message.reply_text(f'Average price of today is: {average_today_price}€ per kwh')
    #update.message.reply_text(f'Lowest price of today is: {lowest_today_price}€ per kwh')
    #update.message.reply_text(f'Highest price of today is: {highest_today_price}€ per kwh')
    #update.message.reply_text('----------------------------------------------------------------------')
    #update.message.reply_text(f'Cheapest time of today was between {cheapest_today_time} hs')
    #update.message.reply_text(f'Expensive time of today was between {expensive_today_time} hs')

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

        # next scraper
        # ----------------------------------------------------------

    # /Users/valentin/github/Ironhack/energy_bot/tomorrow_data_for_testing.csv

    now = datetime.datetime.now().strftime("%I:%M %p")
    #Backup comment as a reminder
    update.message.reply_text(f'Its {now} right now. Tomorrow prices for Spain can only be checked after 8:15 PM GMT+2. Come back later if you get zero values.')

    url = 'https://tarifaluzhora.es/info/precio-kwh-manana'

    headers= {'Accept-Encoding':'gzip, deflate',
                  'Accept-Language':'en-US,en;q=0.9',
                  'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'}

    response = requests.get(url, headers = headers)
    response.status_code
    soup = BeautifulSoup(response.content)


    tomorrow_prices_df = pd.read_html(url)[0]
    tomorrow_prices_df['Hora'] = tomorrow_prices_df['Hora'].str.replace("h","")
    tomorrow_prices_df['Península,  Baleares y Canarias'] = tomorrow_prices_df['Península,  Baleares y Canarias'].str.replace('€/kWh','').replace(',','.')
    tomorrow_prices_df['Península,  Baleares y Canarias'] = tomorrow_prices_df['Península,  Baleares y Canarias'].str.replace(',','.')
    tomorrow_prices_df['Península,  Baleares y Canarias'] = tomorrow_prices_df['Península,  Baleares y Canarias'].str.strip()
    tomorrow_prices_df['Ceuta y Melilla'] = tomorrow_prices_df['Ceuta y Melilla'].str.replace('€/kWh','').replace(',','.')
    tomorrow_prices_df['Ceuta y Melilla'] = tomorrow_prices_df['Ceuta y Melilla'].str.replace(',','.')
    tomorrow_prices_df['Ceuta y Melilla'] = tomorrow_prices_df['Ceuta y Melilla'].str.strip()
    tomorrow_prices_df[['Península,  Baleares y Canarias','Ceuta y Melilla']] = tomorrow_prices_df[['Península,  Baleares y Canarias','Ceuta y Melilla']].astype(float)
    tomorrow_prices_df = tomorrow_prices_df.rename(columns={'Hora':'Hour','Península,  Baleares y Canarias': 'Península, Baleares y Canarias (in €/kWh)', 'Ceuta y Melilla': 'Ceuta y Melilla (in €/kWh)'})
    tomorrow_prices_df['Avg Today - Tier 1'] = tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].mean()
    tomorrow_prices_df['Deviation - Tier 1'] = tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].mean() - tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)']
    tomorrow_prices_df['Avg Today - Tier 2'] = tomorrow_prices_df['Ceuta y Melilla (in €/kWh)'].mean()
    tomorrow_prices_df['Deviation - Tier 2'] = tomorrow_prices_df['Ceuta y Melilla (in €/kWh)'].mean() - tomorrow_prices_df['Ceuta y Melilla (in €/kWh)'].mean()
    tomorrow_prices_df['Price Flag - Tier 1'] = tomorrow_prices_df['Deviation - Tier 1'].apply(price_flag)
    tomorrow_prices_df['Price Flag - Tier 2'] = tomorrow_prices_df['Deviation - Tier 2'].apply(price_flag)
    #tomorrow_prices_df


    #test = pd.read_csv('/Users/valentin/github/Ironhack/energy_bot/tomorrow_data_for_testing.csv')

    #tomorrow_prices_df = test

    # Give expensive & cheap hours for tomorrow

    expensive_hour = tomorrow_prices_df[tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'] == tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].max()][['Hour']]
    expensive_hour_tomorrow = str(expensive_hour['Hour'])[:2]

    cheapest_hour = tomorrow_prices_df[tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'] == tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].min()][['Hour']]
    cheapest_hour_tomorrow = str(cheapest_hour['Hour'])[:2]

    average_price_tomorrow = tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].mean()
    lowest_price_tomorrow = tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].min()
    highest_price_tomorrow = tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].max()

    # Comparing change average price, lowest and highest price, cheap and expensive hours -- today vs tomorrow

    average_change_tomorrow_vs_today = (tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].mean()/price_per_hour['Prices'].mean())-1
    lowest_change_tomorrow_vs_today = (tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].min()/price_per_hour['Prices'].min())-1
    highest_change_tomorrow_vs_today = (tomorrow_prices_df['Península, Baleares y Canarias (in €/kWh)'].max()/price_per_hour['Prices'].max())-1

    # Expensive and cheap hours for today and tomorrow
    expensive_hour_today = price_per_hour[price_per_hour['Prices'] == price_per_hour['Prices'].max()][['Hours']]
    cheapest_hour_today = price_per_hour[price_per_hour['Prices'] == price_per_hour['Prices'].min()][['Hours']]

    # Expensive and cheap hours tomorrow list
    list_cheapest_hours_tomorrow = list(tomorrow_prices_df['Hour'][tomorrow_prices_df['Price Flag - Tier 1'] == 'Cheaper'])
    cheapest_hours_tomorrow = ','.join(list_cheapest_hours_tomorrow)

    list_expensive_hours_tomorrow = list(tomorrow_prices_df['Hour'][tomorrow_prices_df['Price Flag - Tier 1'] == 'Expensive'])
    expensive_hours_tomorrow = ','.join(list_expensive_hours_tomorrow)

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    tomorrow_date = tomorrow.strftime('%d-%m-%Y')


    # \U0001F7E2
    #\U0001F631
    #\U00026A0

    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'Today is {today}')
    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'\U0001F449 Average price of today is: {average_today_price}€ per kwh')
    update.message.reply_text(f'\U0001F7E2 Lowest price of today is: {lowest_today_price}€ per kwh')
    update.message.reply_text(f'\U0001F631 Highest price of today is: {highest_today_price}€ per kwh')
    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'\U0001F920 Cheapest time of today was between {cheapest_today_time} hs')
    update.message.reply_text(f'\U0001F628 Most expensive time of today was between {expensive_today_time} hs')
    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'Tomorrow is {tomorrow_date}')
    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'\U0001F449 Average price for tomorrow will be: {average_price_tomorrow}€ per kwh')
    update.message.reply_text(f'\U0001F7E2 Lowest price for tomorrow will be: {lowest_price_tomorrow}€ per kwh')
    update.message.reply_text(f'\U0001F628 Highest price for tomorrow will be: {highest_price_tomorrow}€ per kwh')
    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'\U0001F920 The cheapest time for tomorrow will be {cheapest_hour_tomorrow}, while the cheapest hours will be: {cheapest_hours_tomorrow}')
    update.message.reply_text(f'\U0001F628 Most expensive time for tomorrow will be {expensive_hour_tomorrow} hs, while the most expensive hours for tomorrow will be: {expensive_hours_tomorrow}')
    update.message.reply_text('----------------------------------------------------------------------')
    update.message.reply_text(f'Today vs Tomorrow difference on the average price is {round(average_change_tomorrow_vs_today*100,2)}%')
    update.message.reply_text(f'Today vs Tomorrow difference on the lowest price is {round(lowest_change_tomorrow_vs_today*100,2)}%')
    update.message.reply_text(f'Today vs Tomorrow difference on the highest price is {round(highest_change_tomorrow_vs_today*100,2)}%')
    update.message.reply_text('----------------------------------------------------------------------')

    energy_sqm = (int(user_data['Size of house'])*180)/365
    update.message.reply_text(f'\U0001F50C kWh of estimated heating consumption for the size of your house is {energy_sqm}.')

    total_energy= (int(user_data["Washing machine"]) * 2 + int(user_data["Oven"]) + int(user_data["Heater"]) * 2)/1000
    update.message.reply_text(f'kWh of total consumption of your appliances: {total_energy}')
    savings = total_energy * (float(highest_today_price) - float(lowest_today_price))
    update.message.reply_text(f'€ of estimated savings: {savings}')
    update.message.reply_text('----------------------------------------------------------------------')

    savings = total_energy * (float(highest_price_tomorrow) - float(lowest_price_tomorrow))
    update.message.reply_text(f'\U0001F4B0 € of estimated savings for tomorrow if you pick the cheapest time: {savings}')

    user_data.clear()

    return ConversationHandler.END


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
