from django.urls import path
from .views import *
from django.views.generic.base import RedirectView

urlpatterns = [
    path('home/', home,name = 'home_page'),
    
    path('',RedirectView.as_view(url = '/home')),
    
    path('create_friend/', create_friend,name = 'create_friend'),
    
    path('friend_list/', friend_list,name = 'friend_list'),
    
    path('chat/<str:room_name>/', start_chat, name='start_chat'),
]
