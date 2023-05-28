from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save
from .models import ChatSession,ChatMessage,Profile,UserChat
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

@receiver(post_save,sender=ChatSession)
def sender_receiver_no_same(sender,instance,created,**kwargs):
    if created:
        if instance.user1 == instance.user2:
            raise ValidationError("Sender and Receiver are not same!!",code='Invalid')

@receiver(post_save,sender=User)
def at_ending_save(sender,instance,created,**kwargs):
    if created:
        Profile.objects.create(user = instance)
        rm_reply = {"room_ids" : []}
        UserChat.objects.create(user = instance,remain_reply = rm_reply)