from channels.generic.websocket import AsyncWebsocketConsumer
import json
from datetime import datetime
from chat_app.models import ChatSession, ChatMessage
from channels.db import database_sync_to_async
import uuid
from .models import Profile
from django.db.models import Q


MESSAGE_MAX_LENGTH = 10

MESSAGE_ERROR_TYPE = {
    "MESSAGE_OUT_OF_LENGTH": 'MESSAGE_OUT_OF_LENGTH',
    "UN_AUTHENTICATED": 'UN_AUTHENTICATED',
    "INVALID_MESSAGE": 'INVALID_MESSAGE',
}

MESSAGE_TYPE = {
    "WENT_ONLINE": 'WENT_ONLINE',
    "WENT_OFFLINE": 'WENT_OFFLINE',
    "IS_TYPING": 'IS_TYPING',
    "NOT_TYPING": 'NOT_TYPING',
    "MESSAGE_COUNTER": 'MESSAGE_COUNTER',
    "OVERALL_MESSAGE_COUNTER": 'OVERALL_MESSAGE_COUNTER',
    "TEXT_MESSAGE": 'TEXT_MESSAGE',
    "MESSAGE_READ": 'MESSAGE_READ',
    "ALL_MESSAGE_READ": 'ALL_MESSAGE_READ',
    "ERROR_OCCURED": 'ERROR_OCCURED'
}

class PersonalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'personal__{self.room_name}'
        self.user = self.scope['user']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        if self.scope["user"].is_authenticated:
            await self.accept()
        else:
            await self.close(code=4001)
            
    async def disconnect(self, code):
        self.set_offline()
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('msg_type')
        user_id = data.get('user_id')
        
        if msg_type == MESSAGE_TYPE['WENT_ONLINE']:
            users_room_id = await self.set_online(user_id)
            for room_id in users_room_id:
                await self.channel_layer.group_send(
                    f'personal__{room_id}',
                    {
                    'type': 'user_online',
                    'user_name' : self.user.username
                    }
                )
        elif msg_type == MESSAGE_TYPE['WENT_OFFLINE']:
            users_room_id = await self.set_offline(user_id)
            for room_id in users_room_id:
                await self.channel_layer.group_send(
                    f'personal__{room_id}',
                    {
                    'type': 'user_offline',
                    'user_name' : self.user.username
                    }
                )
            
    async def user_online(self,event):
        await self.send(text_data=json.dumps({
            'msg_type': MESSAGE_TYPE['WENT_ONLINE'],
            'user_name' : event['user_name']
        }))
        
    async def message_counter(self, event):
        overall_unread_msg = await self.count_unread_overall_msg(event['current_user_id'])
        await self.send(text_data=json.dumps({
            'msg_type': MESSAGE_TYPE['MESSAGE_COUNTER'],
            'user_id': event['user_id'],
            'overall_unread_msg' : overall_unread_msg
        }))

    async def user_offline(self,event):
        await self.send(text_data=json.dumps({
            'msg_type': MESSAGE_TYPE['WENT_OFFLINE'],
            'user_name' : event['user_name']
        }))
    
    @database_sync_to_async
    def set_online(self,user_id):
        Profile.objects.filter(user__id = user_id).update(is_online = True)
        user_all_friends = ChatSession.objects.filter(Q(user1 = self.user) | Q(user2 = self.user))
        user_id = []
        for ch_session in user_all_friends:
            user_id.append(ch_session.user2.id) if self.user.username == ch_session.user1.username else user_id.append(ch_session.user1.id)
        return user_id

    @database_sync_to_async
    def set_offline(self,user_id):
        Profile.objects.filter(user__id = user_id).update(is_online = False)
        user_all_friends = ChatSession.objects.filter(Q(user1 = self.user) | Q(user2 = self.user))
        user_id = []
        for ch_session in user_all_friends:
            user_id.append(ch_session.user2.id) if self.user.username == ch_session.user1.username else user_id.append(ch_session.user1.id)
        return user_id

    @database_sync_to_async
    def count_unread_overall_msg(self,user_id):
        return ChatMessage.count_overall_unread_msg(user_id)
    

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = self.room_name
        self.user = self.scope['user']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        if self.scope["user"].is_authenticated:
            await self.accept()
        else:
            await self.accept()
            await self.send(text_data=json.dumps({
                "msg_type": MESSAGE_TYPE['ERROR_OCCURED'],
                "error_message": MESSAGE_ERROR_TYPE["UN_AUTHENTICATED"],
                "user": self.user.username,
            }))
            await self.close(code=4001)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        msg_type = data.get('msg_type')
        user = data.get('user')

        if msg_type == MESSAGE_TYPE['TEXT_MESSAGE']:
            if len(message) <= MESSAGE_MAX_LENGTH:
                msg_id = uuid.uuid4()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'user': user,
                        'msg_id' : str(msg_id)
                    }
                )
                current_user_id = await self.save_text_message(msg_id,message)
                await self.channel_layer.group_send(
                    f'personal__{current_user_id}',
                    {
                        'type': 'message_counter',
                        'user_id' : self.user.id,
                        'current_user_id' : current_user_id
                    }
                )
            else:
                await self.send(text_data=json.dumps({
                    'msg_type': MESSAGE_TYPE['ERROR_OCCURED'],
                    'error_message': MESSAGE_ERROR_TYPE["MESSAGE_OUT_OF_LENGTH"],
                    'message': message,
                    'user': user,
                    'timestampe': str(datetime.now()),
                }))
        elif msg_type == MESSAGE_TYPE['MESSAGE_READ']:
            msg_id = data['msg_id']
            await self.msg_read(msg_id)
            await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                    'type': 'msg_as_read',
                    'msg_id': msg_id,
                    'user' : user
                    }
                )  
        elif msg_type == MESSAGE_TYPE['ALL_MESSAGE_READ']:
            await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                    'type': 'all_msg_read',
                    'user' : user,
                    }
                )
            await self.read_all_msg(self.room_name[5:],user)
        elif msg_type == MESSAGE_TYPE['IS_TYPING']:
            await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                    'type': 'user_is_typing',
                    'user' : user,
                    }
                )
        elif msg_type == MESSAGE_TYPE["NOT_TYPING"]:
            await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                    'type': 'user_not_typing',
                    'user' : user,
                    }
                )

    # Receive message from room group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'msg_type': MESSAGE_TYPE['TEXT_MESSAGE'],
            'message': event['message'],
            'user': event['user'],
            'timestampe': str(datetime.now()),
            'msg_id' : event["msg_id"]
        }))

    async def msg_as_read(self,event):
        await self.send(text_data=json.dumps({
            'msg_type': MESSAGE_TYPE['MESSAGE_READ'],
            'msg_id': event['msg_id'],
            'user' : event['user']
        }))

    async def all_msg_read(self,event):
        await self.send(text_data=json.dumps({
            'msg_type': MESSAGE_TYPE['ALL_MESSAGE_READ'],
            'user' : event['user']
        }))

    async def user_is_typing(self,event):
        await self.send(text_data=json.dumps({
            'msg_type': MESSAGE_TYPE['IS_TYPING'],
            'user' : event['user']
        }))

    async def user_not_typing(self,event):
        await self.send(text_data=json.dumps({
            'msg_type': MESSAGE_TYPE['NOT_TYPING'],
            'user' : event['user']
        }))

    @database_sync_to_async
    def save_text_message(self,msg_id,message):
        session_id = self.room_name[5:]
        session_inst = ChatSession.objects.select_related('user1', 'user2').get(id=session_id)
        message_json = {
            "msg": message,
            "read": False,
            "timestamp": str(datetime.now()),
            session_inst.user1.username: False,
            session_inst.user2.username: False
        }
        ChatMessage.objects.create(id = msg_id,chat_session=session_inst, user=self.user, message_detail=message_json)
        return session_inst.user2.id if self.user == session_inst.user1 else session_inst.user1.id
    
    @database_sync_to_async
    def msg_read(self,msg_id):
        return ChatMessage.meassage_read_true(msg_id)

    @database_sync_to_async
    def read_all_msg(self,room_id,user):
        return ChatMessage.all_msg_read(room_id,user)