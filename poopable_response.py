class PoopableResponse:

    def __init__(self, channel, poopable):
        self.channel = channel
        self.username = "Poopable"
        self.icon_emoji = ":happy:"
        self.timestamp = ""
        self.poopable = poopable

    def get_message_payload(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": [
                *self._get_poopable_status_block(self.poopable)
            ],
        }

    def _get_poopable_status_block(self, poopable):
        text = (
            self._get_status_sentence(
                poopable_name=poopable['name'], open=poopable['opened'])
        )
        return self._get_task_block(text)

    @staticmethod
    def _get_task_block(text):
        return [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        ]

    @staticmethod
    def _get_status_sentence(poopable_name: str, open: bool):
        return f"{':runner:' if open else ':lock:'} The door of {poopable_name} is {'opened' if open else 'closed'}"
