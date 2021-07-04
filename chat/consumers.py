# chat/consumers.py
import json
#from asgiref.sync import async_to_sync
#from channels.generic.websocket import WebsocketConsumer

from channels.generic.websocket import AsyncWebsocketConsumer #Rewrite the consumer to be asynchronous

class ChatConsumer(AsyncWebsocketConsumer):
    '''
    ChatConsumer now inherits from AsyncWebsocketConsumer rather than WebsocketConsumer
    '''
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        '''
        consumer에게 WebSocket 연결을 연 chat/routing.py의 URL 경로에서 'room_name' 매개 변수를 가져옵니다.
        모든 소비자는 특히 URL 경로의 위치 또는 키워드 인수와 현재 인증된 사용자(있는 경우)를 포함하여 연결에 대한 정보를 포함하는 scope를 가집니다.
        '''
        self.room_group_name = 'chat_%s' % self.room_name
        '''
        사용자가 지정한 룸 이름에서 직접 채널 group 이름을 구성합니다.
        group 이름에는 문자, 숫자, 하이픈 및 마침표만 포함될 수 있습니다.
        '''

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        '''
        group에 참여합니다.
        ChatConsumer는 동기 웹 소켓 consumer이지만 비동기 cahnnel layer 메서드를 호출하기 때문에 async_to_sync()로 감싸줘야 ,한다. (모든 channel layer 메서드는 비동기식입니다.)
        group 이름은 ASCII 영숫자, 하이픈 및 마침표로만 제한됩니다
        '''

        await self.accept()
        '''
        WebSocket 연결을 수락합니다.
        connect() 메서드 내에서 accept()을 호출하지 않으면 연결이 거부되고 닫힙니다. 예를 들어 요청한 사용자에게 요청된 작업을 수행할 수 있는 권한이 없기 때문에 연결을 거부할 수 있습니다.
        연결을 수락하도록 선택한 경우 accept()를 connect()의 마지막 작업으로 호출하는 것이 좋습니다.
        '''

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        '''
        group에 나갑니다.
        '''

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
        '''
        group에 이벤트를 보냅니다.
        이벤트에는 이벤트를 수신하는 consumer에게 호출해야 하는 메서드의 이름에 해당하는 특수 'type' 키가 있습니다.
        '''

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    '''All methods are async def rather than just def.'''
    '''await is used to call asynchronous functions that perform I/O.'''
    '''async_to_sync is no longer needed when calling methods on the channel layer.'''

"""
사용자가 메시지를 게시하면 JavaScript 기능은 WebSocket을 통해 Chat Consumer로 메시지를 전송합니다.
Chat Consumer는 이 메시지를 수신하여 room name에 해당하는 group으로 전달합니다.
그러면 동일한 group(따라서 같은 room에 있는)의 모든 채팅 consumer가 메시지를 받게 됩니다.
웹 소켓을 통해 다시 JavaScript로 전달하면 채팅 로그에 추가됩니다.
로그에 추가될 뿐 데이터베이스에 저장되지 않아 새로고침을 하면 로그는 전부 지워진다.
"""