import json
from datetime import datetime
from .consumers import MESSAGE_TYPE,MESSAGE_ERROR_TYPE

async def send_chat_message(self, event):
    await self.send(text_data=json.dumps({
        'msg_type': MESSAGE_TYPE['TEXT_MESSAGE'],
        'message': event['message'],
        'user': event['user'],
        'timestampe': str(datetime.now()),
        'msg_id' : event["msg_id"]
    }))
    
async def send_msg_as_read(self,event):
    await self.send(text_data=json.dumps({
        'msg_type': MESSAGE_TYPE['MESSAGE_READ'],
        'msg_id': event['msg_id'],
        'user' : event['user']
    }))
    
async def send_all_msg_read(self,event):
    await self.send(text_data=json.dumps({
        'msg_type': MESSAGE_TYPE['ALL_MESSAGE_READ'],
        'user' : event['user']
    }))
    
async def send_user_is_typing(self,event):
    await self.send(text_data=json.dumps({
        'msg_type': MESSAGE_TYPE['IS_TYPING'],
        'user' : event['user']
    }))

async def send_user_not_typing(self,event):
    await self.send(text_data=json.dumps({
        'msg_type': MESSAGE_TYPE['NOT_TYPING'],
        'user' : event['user']
    }))
    
async def send_auth_error(self):
    await self.send(text_data=json.dumps({
        "msg_type": MESSAGE_TYPE['ERROR_OCCURED'],
        "error_message": MESSAGE_ERROR_TYPE["UN_AUTHENTICATED"],
        "user": self.user.username,
    }))

async def send_invalid_user(self,event):
    await self.send(text_data=json.dumps({
        "msg_type": MESSAGE_TYPE['ERROR_OCCURED'],
        "error_message": MESSAGE_ERROR_TYPE["INVALID_USER"],
        "user": event['username'],
    }))
    
async def send_user_online(self,event):
    await self.send(text_data=json.dumps({
        'msg_type': MESSAGE_TYPE['WENT_ONLINE'],
        'user_name' : event['user_name']
    }))
    
async def send_message_counter(self, event,overall_unread_msg):
    await self.send(text_data=json.dumps({
        'msg_type': MESSAGE_TYPE['MESSAGE_COUNTER'],
        'user_id': event['user_id'],
        'overall_unread_msg' : overall_unread_msg
    }))
    
async def send_user_offline(self,event):
    await self.send(text_data=json.dumps({
        'msg_type': MESSAGE_TYPE['WENT_OFFLINE'],
        'user_name' : event['user_name']
    }))