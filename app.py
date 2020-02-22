from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from slack import WebClient
from slackeventsapi import SlackEventAdapter
from flask import request
import ssl as ssl_lib
import certifi
import json
import pymysql.cursors

from onboarding_tutorial import OnboardingTutorial
from poopable_response import PoopableResponse

import os
import logging
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
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{NAME}:{PASSWORD}@{RDS_HOST}:{RDS_PORT}/{DB_NAME}"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

#initialize db models

class Poopable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, default="")
    last_update = db.Column(db.String(10), nullable=False, default="0000000000")
    opened = db.Column(db.Boolean, nullable=False, default='False')

slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

# Initialize a Web API client
slack_web_client = WebClient(token=SLACK_BOT_TOKEN)

onboarding_tutorials_sent = {}

poopables_log = []

poopables = {}

db_poopables = Poopable.query.all()

for db_poopable in db_poopables:
    poopables[db_poopable.id] = {
        "id": db_poopable.id,
        "open": db_poopable.opened,
        "last_update": db_poopable.last_update,
    }

subscriptions = {}

def update_poopable_by_event(event):
    target_poopable = poopables[int(event['poopable_id'])]
    if event['event_type'] == 'door':
        target_poopable['open'] = True if event['value'] == 'open' else False
        target_poopable['last_update'] = event['time']

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
    onboarding_tutorial = OnboardingTutorial(channel)

    message = onboarding_tutorial.get_message_payload()

    response = slack_web_client.chat_postMessage(**message)

    onboarding_tutorial.timestamp = response["ts"]

    if channel not in onboarding_tutorials_sent:
        onboarding_tutorials_sent[channel] = {}
    onboarding_tutorials_sent[channel][user_id] = onboarding_tutorial

def push_poopable_status(channel: str):
    poopable_response = PoopableResponse(channel, poopables)

    message = poopable_response.get_message_payload()

    response = slack_web_client.chat_postMessage(**message)

@slack_events_adapter.on("message")
def message(payload):
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


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    app.run(port=3000, debug=True)