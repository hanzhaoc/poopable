class OnboardingTutorial:
    """Constructs the onboarding message and stores the state of which tasks were completed."""

    WELCOME_BLOCK = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "Welcome to Poopable! :wave: Your Poopable is always one slack away. :blush:\n\n"
            ),
        },
    }

    SELECT_POOPABLE_BLOCK = {
        "type": "section",
        "block_id": "section678",
        "text": {
            "type": "mrkdwn",
            "text": "Pick a default poopable device that you want to subscribe"
        },
        "accessory": {
            "action_id": "text1234",
            "type": "static_select",
            "placeholder": {
                "type": "plain_text",
                "text": "Select a poopable device"
            },
            "options": [
                {
                    "text": {
                        "type": "plain_text",
                        "text": "130-middle-male"
                    },
                    "value": "1"
                },
            ]
        }
    }

    SUCCESSFULLY_SUBSCRIBE_BLOCK = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "Your default subscribed device is set up. You can use command `stop` to unsubscribe. :shit:\n\n"
            ),
        },
    }

    DIVIDER_BLOCK = {"type": "divider"}

    def __init__(self, channel):
        self.channel = channel
        self.username = "pythonboardingbot"
        self.icon_emoji = ":robot_face:"
        self.timestamp = ""
        self.reaction_task_completed = False
        self.pin_task_completed = False

    def get_message_payload(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": [
                self.WELCOME_BLOCK,
                self.SELECT_POOPABLE_BLOCK,
            ],
        }

    def get_successfully_subscribe_message_payload(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": [
                self.SUCCESSFULLY_SUBSCRIBE_BLOCK,
            ],
        }
