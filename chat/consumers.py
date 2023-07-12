from channels.generic.websocket import WebsocketConsumer
import json

class ChatConsumer(WebsocketConsumer):
    messages = []

    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        ChatConsumer.messages = []

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        ChatConsumer.messages.append(message)

        self.send(text_data=json.dumps({
            'messages': ChatConsumer.messages
        }))
