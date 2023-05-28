from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from collections import Counter


class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name = 'profile_detail')
    '''
       Add other fields...
    '''
    is_online = models.BooleanField(default = False)
    
    class Meta:
        verbose_name = '1. Profile'

class UserChat(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name = 'user_chat')
    chat_provide = models.IntegerField(default = 25)
    price = models.CharField(default = '5(USD)',max_length=25)
    remain_reply = models.JSONField(default=dict)   # By using this we can calculate the reply rate
    
    class Meta:
        verbose_name = '2. Chat'
    
    def __str__(self):
        return '%s(%s)' %(self.user.username,self.chat_provide)

    @property
    def calculate_reply_rate(self):
        room_ids = self.remain_reply.get('room_ids')
        if not room_ids:
            final_rate = 100
            remain_room_ids = []
            return final_rate,remain_room_ids
        else:
            a = dict(Counter(room_ids))
            remain_room_ids = []
            _total = 0
            for key,value in a.items():
                if value >= 2:
                    remain_room_ids.append(key)
                    _total += value
            final_rate = 1 if _total >= 300 else 100 - _total * (1/3)
            return final_rate,remain_room_ids

class ChatSession(models.Model):
    user1 = models.ForeignKey(User,on_delete=models.CASCADE,related_name='user1_name')
    user2 = models.ForeignKey(User,on_delete=models.CASCADE,related_name='user2_name')
    user1_remain_chat = models.IntegerField(help_text='user1\'s remain chats')
    user2_remain_chat = models.IntegerField(help_text='user2\'s remain chats')
    updated_on = models.DateTimeField(auto_now = True)
    
    class Meta:
        unique_together = (("user1", "user2"))
        verbose_name = '2. Chat Message'
        
    def __str__(self):
        return '%s_%s' %(self.user1.username,self.user2.username)
        
    @property
    def room_group_name(self):
        return f'chat_{self.id}'

    @staticmethod
    def chat_session_exists(user1,user2):
        return ChatSession.objects.filter(Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)).first()
    
    @staticmethod
    def create_if_not_exists(user1,user2):
        res = ChatSession.chat_session_exists(user1,user2)
        return False if res else ChatSession.objects.create(user1=user1,user2=user2,user1_remain_chat = 20,user2_remain_chat = 20)
    
from .encription import Crypto
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key = True,editable = False)
    chat_session = models.ForeignKey(ChatSession,on_delete=models.CASCADE,related_name='user_messages')
    user = models.ForeignKey(User, verbose_name='message_sender',on_delete=models.CASCADE)
    message_detail = models.JSONField()

    class Meta:
        ordering = ['-message_detail__timestamp']
    
    def __str__(self):
        return '%s' %(self.message_detail["timestamp"])

    def save(self,*args,**kwargs):
        if self.user != self.chat_session.user1 and self.user != self.chat_session.user2:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{self.chat_session.id}',
                {
                    'type': 'invalid_user',
                    'username' : self.user.username
                }
            )
        else:
            super().save(*args, **kwargs)
            ChatSession.objects.get(id = self.chat_session.id).save()

    @property
    def decript_chat(self):
        dn = Crypto(self.message_detail['msg']).decrypt()
        return dn

    @staticmethod
    def count_overall_unread_msg(user_id):
        total_unread_msg = 0
        user_all_friends = ChatSession.objects.filter(Q(user1__id = user_id) | Q(user2__id = user_id))
        for ch_session in user_all_friends:
            un_read_msg_count = ChatMessage.objects.filter(chat_session = ch_session.id,message_detail__read = False).exclude(user__id = user_id).count()        
            total_unread_msg += un_read_msg_count
        return total_unread_msg

    @staticmethod
    def meassage_read_true(message_id):
        msg_inst = ChatMessage.objects.filter(id = message_id).first()
        if msg_inst:
            msg_inst.message_detail['read'] = True
            msg_inst.save(update_fields = ['message_detail',])
        return None

    @staticmethod
    def all_msg_read(room_id,user):
        all_msg = ChatMessage.objects.filter(chat_session = room_id,message_detail__read = False).exclude(user__username = user)
        for msg in all_msg:
            msg.message_detail['read'] = True
            msg.save(update_fields = ['message_detail',])
        return None

    @staticmethod
    def sender_inactive_msg(message_id):
        return ChatMessage.objects.filter(id = message_id).update(message_detail__Sclr = True)

    @staticmethod
    def receiver_inactive_msg(message_id):
        return ChatMessage.objects.filter(id = message_id).update(message_detail__Rclr = True)