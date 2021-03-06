import argparse

# Requests HTTP lib
import requests

# Flask server imports
from flask import Flask
from flask import request
from flask import Response
import asyncio
# RASA core imports
from rasa.core.agent import Agent
from rasa.core.interpreter import RasaNLUInterpreter
from rasa.core.utils import EndpointConfig
from rasa.core.channels.telegram import TelegramOutput


# Telegram bot API base url
BASE_URL = 'https://api.telegram.org/bot'

# Current Telegram chat
current_chat = None

# Inits Flask
app = Flask(__name__)

# Create a new CLI parser
parser = argparse.ArgumentParser(description='RASA integration with Telegram')
parser.add_argument('--token', type=str, help='Telegram API bot token')
parser.add_argument('--tunnel', type=str, help='URL for the Ngrok tunnel')

# Parse input args
args = parser.parse_args()


# Accept Telegram messages
# The '/' route receives the POST and GET requests from Telegram
@app.route('/', methods=['POST', 'GET'])
def index():
    global current_chat

    if request.method == 'POST':

        # Get message data
        msg = request.get_json()
        chat_id, message, username = parse_msg(msg)
        current_chat = str(chat_id) + '/' + username

        # Get RASA response and send through the API
        response_messages = rasa_response(message, current_chat)
        send_message(current_chat, response_messages)

        # Set the message to be returned
        return Response('OK', status=200)
    else:
        return 'Hello!'


# Accept info messages from a client
# The '/info' route receives the POST request from an external server
# This request should contain the chat_id, response, and question fields
@app.route('/info', methods=['POST'])
def info():
    messages = []

    # Get message data (chat_id, response, and question fields)
    # If you do not know yur chat_id, use the value of the global variable 'current_chat'
    r = request.get_json()
    response_data = r['response']
    chat_id = r['chat_id']
    user_question = r['question']

    # Get the current chat username
    # The sender_id is in the format [chat_id]/[username]
    username = chat_id.split('/')[1]

    # Set the provided response
    messages.append(response_data)

    # Create a Telegram response channel
    telegram_output = TelegramOutput(access_token=args.token)

    # Inform the user on the previous question
    message = 'Hey ' + username + '\n'
    message = message + 'You previously asked: ' + user_question + ' Here is your answer:'
    telegram_output.send_message(chat_id=chat_id, text=message)

    # Send the bot response
    for message in messages:
        telegram_output.send_message(chat_id=chat_id, text=message)

    # Execute an action
    agent.execute_action(sender_id=chat_id, action='action_restart', output_channel=telegram_output,
                         policy='', confidence=1)

    return Response('OK', status=200)


# Extract the chat id and text from a given message
# Returns both values
def parse_msg(message):
    global current_chat
    current_chat = message['message']['chat']['id']
    txt = message['message']['text']
    try:
        username = message['message']['chat']['username']
    except:
        username=''
    return current_chat, txt, username


# Send message through the Telegram API
def send_message(chat_id, messages=None):
    telegram_output = TelegramOutput(access_token=args.token)

    if messages is None:
        messages = []

    # RASA responded
    # Sent the messages through the Telegram API
    if messages:
        for message in messages:
            telegram_output.send_message(chat_id=chat_id, text=message)

    return True


# Get response using RASA
# The handle_message method is responsible for processing the message
def rasa_response(message, chat_id):

    # Get RASA responses for a given message
    responses = asyncio.run(agent.handle_text(message, sender_id=chat_id))
    text = []

    # RASA responded
    if responses:
        for response in responses:
            text.append(response['text'])

    return text


# Load trained models
# Returns the agent created based on the trained models
def rasa_config():

    # Set the actions endpoint
    action_endpoint = EndpointConfig(url='https://alimentos-actions.herokuapp.com/webhook')

    # Load the trained RASA models
    #interpreter = RasaNLUInterpreter('./models/rasa-telegram-app/nlu')
    return Agent.load('./models/20200629-233250.tar.gz', action_endpoint=action_endpoint)


# Sets the Ngrok configuration
# Starts Ngrok and sets a new tunnel to Telegram
def ngrok_config():

    # Set the tunnel to Telegram
    tunnel_url = BASE_URL + args.token + '/setWebhook?url=' + args.tunnel
    r = requests.get(tunnel_url)
    print('Telegram Webhook: ' + r.json()['description'])


# Entry point
if __name__ == '__main__':

    # Load RASA models
    print('Loading RASA models...')
    agent = rasa_config()

    # Setup Ngrok
    print('\nSetting the Telegram Ngrok webhook...')
    ngrok_config()

    # Setup Flask
    print('\nStarting the Flask server...')
    app.run()
