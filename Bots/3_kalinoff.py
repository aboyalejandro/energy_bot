import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
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

AC, HOUSE, OVEN, HEATER = range(4)


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their appliances."""
    reply_keyboard = [['Yes', 'No']]

    update.message.reply_text(
        'Hi! My name is Energy Bot. I will hold a conversation with you. '
        'Send /cancel to stop talking to me.\n\n'
        'Do you have an A/C at home?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Yes or No?'
        ),
    )

    return AC


def ac(update: Update, context: CallbackContext) -> int:
    """Stores the selected gender and asks for a photo."""
    reply_keyboard = [['<30qm', '<50qm', '<80qm']]
    own_ac = update.message.from_user
    logger.info("Do you have A/C of %s: %s", own_ac.first_name, update.message.text)
    update.message.reply_text(
        'What is the size of your appartment/house?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='<30qm or <50qm or <80qm?'
        ),
    )

    return ConversationHandler.END

def oven(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their appliances."""
    reply_keyboard = [['Yes', 'No']]

    update.message.reply_text(
        'Hi! My name is Energy Bot. I will hold a conversation with you. '
        'Send /cancel to stop talking to me.\n\n'
        'Do you have oven at home?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Yes or No?'
        ),
    )

    return ConversationHandler.END




def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("5374346481:AAFjRjPVVVVdyqatr0f1wFaPQphcRaEsOrc")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AC: [MessageHandler(Filters.regex('^(Yes|No)$'), ac)],
            #HOUSE: [MessageHandler(Filters.regex('^(<30qm|<50qm|<80qm)$'), house)],
            #OVEN: [MessageHandler(Filters.regex('^(Yes|No)$'), oven)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
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
