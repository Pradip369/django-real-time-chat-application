from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import *
from django.http.response import HttpResponse, HttpResponseRedirect
from django.contrib import messages

# def room_name(request):
#     return render(request, 'chat/enter_room_name.html')
# def room(request, room_name):
#     return render(request, 'chat/chat.html', {'room_name': room_name})

def home(request):
    unread_msg = ChatMessage.count_overall_unread_msg(request.user.id)
    return render(request, 'chat/home.html',{"unread_msg" : unread_msg})

@login_required
def create_friend(request):
    user_1 = request.user
    if request.GET.get('id'):
        user2_id = request.GET.get('id')
        user_2 = get_object_or_404(User,id = user2_id)
        get_create = ChatSession.create_if_not_exists(user_1,user_2)
        if get_create:
            messages.add_message(request,messages.SUCCESS,f'{user_2.username} successfully added in your chat list!!')
        else:
            messages.add_message(request,messages.SUCCESS,f'{user_2.username} already added in your chat list!!')
        return HttpResponseRedirect('/create_friend')
    else:
        user_all_friends = ChatSession.objects.filter(Q(user1 = user_1) | Q(user2 = user_1))
        user_list = []
        for ch_session in user_all_friends:
            user_list.append(ch_session.user1.id)
            user_list.append(ch_session.user2.id)
        all_user = User.objects.exclude(Q(username=user_1.username)|Q(id__in = list(set(user_list))))
    return render(request, 'chat/create_friend.html',{'all_user' : all_user})


@login_required
def friend_list(request):
    user_inst = request.user
    user_all_friends = ChatSession.objects.filter(Q(user1 = user_inst) | Q(user2 = user_inst)).select_related('user1','user2').order_by('-updated_on')
    all_friends = []
    for ch_session in user_all_friends:
        user,user_inst = [ch_session.user2,ch_session.user1] if request.user.username == ch_session.user1.username else [ch_session.user1,ch_session.user2]
        un_read_msg_count = ChatMessage.objects.filter(chat_session = ch_session.id,message_detail__read = False).exclude(user = user_inst).count()        
        data = {
            "user_name" : user.username,
            "room_name" : ch_session.room_group_name,
            "un_read_msg_count" : un_read_msg_count,
            "status" : user.profile_detail.is_online,
            "user_id" : user.id
        }
        all_friends.append(data)

    return render(request, 'chat/friend_list.html', {'user_list': all_friends})

@login_required
def start_chat(request,room_name):
    current_user = request.user
    try:
        check_user = ChatSession.objects.filter(Q(id = room_name[5:])&(Q(user1 = current_user) | Q(user2 = current_user)))
    except Exception:
        return HttpResponse("Something went wrong!!!")
    if check_user.exists():
        chat_user_pair = check_user.first()
        opposite_user = chat_user_pair.user2 if chat_user_pair.user1.username == current_user.username else chat_user_pair.user1
        fetch_all_message = ChatMessage.objects.filter(chat_session__id = room_name[5:]).order_by('message_detail__timestamp')
        return render(request,'chat/start_chat.html',{'room_name' : room_name,'opposite_user' : opposite_user,'fetch_all_message' : fetch_all_message})
    else:
        return HttpResponse("You have't permission to chatting with this user!!!")

def get_last_message(request):
    session_id = request.data.get('room_id')
    qs = ChatMessage.objects.filter(chat_session__id = session_id)[10]
    return qs