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

users_prefered_poopables = db.Table('users_prefered_poopables',
    db.Column('slack_user_id', db.String(9), db.ForeignKey('user.slack_user_id'), primary_key=True),
    db.Column('poopable_id', db.Integer, db.ForeignKey('poopable.id'), primary_key=True)
)

class Poopable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, default="")
    last_update = db.Column(db.String(10), nullable=False, default="0000000000")
    opened = db.Column(db.Boolean, nullable=False, default='False')

class User(db.Model):
    slack_user_id = db.Column(db.String(9), primary_key=True)
    prefered_poopables = db.relationship('Poopable', secondary=users_prefered_poopables, lazy='subquery',
        backref=db.backref('prefered_by_users', lazy=True))


# Initialize a Web API client
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)
slack_web_client = WebClient(token=SLACK_BOT_TOKEN)

onboarding_tutorials_sent = {}

poopables = {}

db_poopables = Poopable.query.all()

for db_poopable in db_poopables:
    poopables[db_poopable.id] = {
        "id": db_poopable.id,
        "open": db_poopable.opened,
        "last_update": db_poopable.last_update,
        "name": db_poopable.name
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

    app.logger.info(subscriptions)
    app.logger.info("these channels will receive the message")

    for channel_id in subscriptions:
        user = User.query.get(subscriptions[channel_id]['user_id'])
        prefered_poopable = user.prefered_poopables[0]
        target_poopable = poopables[prefered_poopable.id]
        push_poopable_status(channel_id, target_poopable)

    return '', 204

@app.route("/slack/message_actions", methods=["POST"])
def message_actions():

    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Check to see what the user's selection was and update the message accordingly
    # app.logger.info(form_json)
    user_id = form_json.get('user').get('id')
    channel = form_json.get('id')
    value = form_json.get('actions')[0].get('selected_option').get('value')

    user = User.query.get(user_id)
    poopable = Poopable.query.get(int(value))
    app.logger.info(value)
    app.logger.info(int(value))
    app.logger.info(user)
    app.logger.info(poopable)

    user.prefered_poopables.append(poopable)
    db.session.add(poopable)
    db.session.add(user)
    db.session.commit()

    return "", 200

def start_onboarding(user_id: str, channel_id: str):

    #create user and give a default poopable
    exists = db.session.query(db.exists().where(User.slack_user_id == user_id)).scalar()
    if not exists:
        user = User(slack_user_id=user_id)
        db.session.add(user)
        db.session.commit()

    #create on boarding tutorial and sent it to user
    onboarding_tutorial = OnboardingTutorial(channel_id)

    message = onboarding_tutorial.get_message_payload()

    response = slack_web_client.chat_postMessage(**message)

def push_poopable_status(channel: str, poopable):
    poopable_response = PoopableResponse(channel, poopable)

    message = poopable_response.get_message_payload()

    response = slack_web_client.chat_postMessage(**message)

@slack_events_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    time_stamp = event.get('ts')

    if not (event and channel_id and user_id and text and time_stamp): return 'invalid payload', 422

    if text.lower() == 'poop':
        user = User.query.get(user_id)
        prefered_poopables = user and user.prefered_poopables
        app.logger.info(prefered_poopables)
        if user is None:  
            return start_onboarding(user_id, channel_id)
        elif len(prefered_poopables) == 0:
            return start_onboarding(user_id, channel_id)
        else:
            prefered_poopable = user.prefered_poopables[0]
            app.logger.info(prefered_poopable)
            target_poopable = poopables[prefered_poopable.id]
            app.logger.info(target_poopable)
            subscriptions[channel_id] = { "start_time": time_stamp, "user_id":user_id }
            return push_poopable_status(channel_id, target_poopable)
    elif text.lower() == 'stop':
        return subscriptions.pop(channel_id, None)
    else:
        return


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    app.run(port=5000, debug=True)