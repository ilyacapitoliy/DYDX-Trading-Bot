import requests
from decouple import config
import telegram
from telegram.ext import Updater, CommandHandler
import subprocess

# Send Mesage Technical Info about Launch, Errors etc.
def send_message(message):

    bot_token_log = config("TELEGRAM_TOKEN_LOG")
    chat_id = config("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token_log}/sendMessage?chat_id={chat_id}&text={message}"
    res = requests.get(url)
    if res.status_code == 200:
        return "sent"
    else:
        return "failed"

# Send Mesage Technical Info about Launch, Errors etc.
def send_message_main(message_1):

    bot_token_main = config("TELEGRAM_TOKEN_MAIN")
    chat_id = config("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token_main}/sendMessage?chat_id={chat_id}&text={message_1}"
    res = requests.get(url)
    if res.status_code == 200:
        return "sent"
    else:
        return "failed"
    
# Send Mesage Technical Info about Launch, Errors etc.
def send_message_berta(message_2):

    bot_token_berta = config("TELEGRAM_TOKEN_BERTA")
    chat_id = config("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token_berta}/sendMessage?chat_id={chat_id}&text={message_2}"
    res = requests.get(url)
    if res.status_code == 200:
        return "sent"
    else:
        return "failed"
    
    

# # Create a bot instance with your API token
# bot = telegram.Bot(token='TELEGRAM_TOKEN_BERTA')

# # Define the function that will launch the code on the remote server
# def launch_code(update, context):
#     # Replace "your-command-here" with the actual command to launch your Python code on the remote server
#     cmd = "launch"
    
#     # Use the subprocess module to launch the command
#     process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    
#     # Send a message to the user to indicate that the code has been launched
#     bot.send_message(chat_id=update.message.chat_id, text="Code launched on the remote server.")

# # Create an Updater instance and add the command handler for the "/start" command
# updater = Updater(token='TELEGRAM_TOKEN_BERTA', use_context=True)
# updater.dispatcher.add_handler(CommandHandler('start', launch_code))

# # Start the bot
# updater.start_polling()
    
