from bs4 import BeautifulSoup
import requests
import schedule
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def bot_send_text(bot_message):

    bot_token = '5374346481:AAFjRjPVVVVdyqatr0f1wFaPQphcRaEsOrc'
    bot_chatID = '163796728'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()


def btc_scraping():
    url = requests.get('https://awebanalysis.com/es/coin-details/bitcoin/')
    soup = BeautifulSoup(url.content, 'html.parser')
    result = soup.find('td', {'class': 'wbreak_word align-middle coin_price'})
    format_result = result.text

    return format_result


def report():
    btc_price = f'The current Bitcoin price is: {btc_scraping()}'
    bot_send_text(btc_price)


if __name__ == '__main__':
    report()
