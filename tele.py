from flask import Flask, copy_current_request_context
from flask import Flask, request
import telegram
import asyncio
from rasa_core.agent import Agent
from rasa_core.utils import EndpointConfig
TOKEN = '1135010132:AAFOtVvCONRWjUl2rhzLHP6kcECBVUSxhig'
app = Flask(__name__)

#interpreter = Interpreter.load('./models/alimentos/nlu')

agent = Agent.load('./models/20200626-200236.tar.gz', action_endpoint=EndpointConfig(url="https://alimentos-actions.herokuapp.com/webhook"))
def applyAi(message):
    responses = asyncio.run(agent.handle_message(message))
    text = response["text"]
    #if responses:
    #    for response in responses:
    #        text.append(response["text"]
    return text
bot = telegram.Bot(token=TOKEN)
@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()
    print("got text message :", text)

    response = applyAi(text)
    bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)

    return 'ok'
URL='https://alimentoscharis.herokuapp.com/'
@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/')
def index():
    return '.'


if __name__ == '__main__':
    app.run(threaded=True)