from .models import ChatSession,Profile,UserChat,ChatMessage
from datetime import datetime
from django.db.models import Q
from .encription import Crypto

def db_save_text_message(self,msg_id,message):
        session_id = self.room_name[5:]
        session_inst = ChatSession.objects.select_related('user1', 'user2').get(id=session_id)
        en_msg = Crypto(message).encrypt()
        
        message_json = {
            "msg": en_msg,
            "read": False,
            "timestamp": str(datetime.now()),
            session_inst.user1.username: False,
            session_inst.user2.username: False
        }
        ChatMessage.objects.create(id = msg_id,chat_session=session_inst, user=self.user, message_detail=message_json)
        
        if self.user.id == session_inst.user1.id:
            session_inst.user1_remain_chat -= 1
            session_inst.save(update_fields = ['user1_remain_chat'])
            receiver_id = session_inst.user2.id
            opposite_chat_inst = UserChat.objects.get(user = session_inst.user2)
        else:            
            session_inst.user2_remain_chat -= 1
            session_inst.save(update_fields = ['user2_remain_chat'])
            receiver_id = session_inst.user1.id
            opposite_chat_inst = UserChat.objects.get(user = session_inst.user1)

        # Add current room id in opposite user's remain_reply..
        op_room_id = opposite_chat_inst.remain_reply['room_ids'].append(session_id)
        opposite_chat_inst.save(update_fields = ['remain_reply'])

        # Remove current room id in current user's remain_reply..
        current_chat_inst = UserChat.objects.get(user = self.user)
        cr_room_id = current_chat_inst.remain_reply['room_ids']
        while session_id in cr_room_id: cr_room_id.remove(session_id)
        current_chat_inst.save(update_fields = ['remain_reply'])

        return session_inst.user2.id if self.user == session_inst.user1 else session_inst.user1.id

def db_read_all_msg(self,room_id,user):
    return ChatMessage.all_msg_read(room_id,user)

def db_msg_read(self,msg_id):
    return ChatMessage.meassage_read_true(msg_id)

def db_set_online(self,user_id):
    Profile.objects.filter(user__id = user_id).update(is_online = True)
    user_all_friends = ChatSession.objects.filter(Q(user1 = self.user) | Q(user2 = self.user))
    user_id = []
    for ch_session in user_all_friends:
        user_id.append(ch_session.user2.id) if self.user.username == ch_session.user1.username else user_id.append(ch_session.user1.id)
    return user_id

def db_set_offline(self,user_id):
    Profile.objects.filter(user__id = user_id).update(is_online = False)
    user_all_friends = ChatSession.objects.filter(Q(user1 = self.user) | Q(user2 = self.user))
    user_id = []
    for ch_session in user_all_friends:
        user_id.append(ch_session.user2.id) if self.user.username == ch_session.user1.username else user_id.append(ch_session.user1.id)
    return user_id

def db_count_unread_overall_msg(self,user_id):
    return ChatMessage.count_overall_unread_msg(user_id)