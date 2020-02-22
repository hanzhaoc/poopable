import os
import logging
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from flask import request
import ssl as ssl_lib
import certifi
import json
import pymysql.cursors

from onboarding_tutorial import OnboardingTutorial
from poopable_response import PoopableResponse

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
# set globals
RDS_HOST = os.getenv("DB_HOST")
RDS_PORT = int(os.getenv("DB_PORT", 3306))
NAME = os.getenv("DB_USERNAME")
PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Initialize a Flask app to host the events adapter
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

# Initialize a Web API client
slack_web_client = WebClient(token=SLACK_BOT_TOKEN)

onboarding_tutorials_sent = {}

poopables_log = [

]

poopables = {
    1: { "id": 1, "open": False, "last_update": '1581899190'}
}

subscriptions = {}

def update_poopable_by_event(event):
    target_poopable = poopables[int(event['poopable_id'])]
    if event['event_type'] == 'door':
        target_poopable['open'] = True if event['value'] == 'open' else False
        target_poopable['last_update'] = event['time']
    app.logger.info(json.dumps(poopables))

def connect():
    try:
        cursor = pymysql.cursors.DictCursor
        conn = pymysql.connect(RDS_HOST, user=NAME, passwd=PASSWORD, db=DB_NAME, port=RDS_PORT, cursorclass=cursor, connect_timeout=5)
        app.logger.info("SUCCESS: connection to RDS successful")
        return(conn)
    except Exception as e:
        app.logger.exception("Database Connection Error")

@app.route('/', methods=['GET'])
def index():
    connect()
    return '', 200

@app.route('/poopable/event', methods=['POST'])
def receive_poopable_event():
    event = {
        'time': request.json['time'],
        'event_type': request.json['event_type'],
        'value': request.json['value'],
        'poopable_id': request.json['poopable_id']
    }

    app.logger.info('receiving event object: '+ json.dumps(event))
    
    update_poopable_by_event(event)
    poopables_log.append(event)

    app.logger.info(subscriptions)
    app.logger.info("these channels will receive the message")

    for channel_id in subscriptions:
        push_poopable_status(channel_id)

    return '', 204

def start_onboarding(user_id: str, channel: str):
    # Create a new onboarding tutorial.
    onboarding_tutorial = OnboardingTutorial(channel)

    # Get the onboarding message payload
    message = onboarding_tutorial.get_message_payload()

    # Post the onboarding message in Slack
    response = slack_web_client.chat_postMessage(**message)

    # Capture the timestamp of the message we've just posted so
    # we can use it to update the message after a user
    # has completed an onboarding task.
    onboarding_tutorial.timestamp = response["ts"]

    # Store the message sent in onboarding_tutorials_sent
    if channel not in onboarding_tutorials_sent:
        onboarding_tutorials_sent[channel] = {}
    onboarding_tutorials_sent[channel][user_id] = onboarding_tutorial

def push_poopable_status(channel: str):
    # Create a new onboarding tutorial.
    poopable_response = PoopableResponse(channel, poopables)

    # Get the onboarding message payload
    message = poopable_response.get_message_payload()

    # Post the onboarding message in Slack
    response = slack_web_client.chat_postMessage(**message)

@slack_events_adapter.on("message")
def message(payload):
    """Display the onboarding welcome message after receiving a message
    that contains "start".
    """
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    time_stamp = event.get('ts')
    app.logger.info(text)

    app.logger.info(subscriptions)
    if text and text.lower() == "start":
        subscriptions[channel_id] = { "state_time": time_stamp }
        return push_poopable_status(channel_id)
    elif text and text.lower() == "stop":
        subscriptions.pop(channel_id, None)

@app.route('/', methods=['POST'])
def test():
    app.logger.info(SLACK_SIGNING_SECRET)
    app.logger.info(SLACK_BOT_TOKEN)
    app.logger.info(request.json)
    app.logger.info(slack_events_adapter)
    return request.json['challenge']


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    app.run(port=3000, debug=True)