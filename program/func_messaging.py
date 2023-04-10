import requests
from decouple import config

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
    
