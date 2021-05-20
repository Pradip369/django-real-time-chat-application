from django.contrib import admin
from .models import *
from django_admin_inline_paginator.admin import TabularInlinePaginated

class ChatMessageInline(TabularInlinePaginated):
    model = ChatMessage
    can_delete = False
    fields = ('user','message_detail')
    max_num = 0
    readonly_fields = fields
    per_page = 10

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display= ["id","user1","user2",'updated_on']
    search_fields=["id","user1__username","user2_username"]
    list_per_page = 10
    list_display_links = list_display
    inlines = [ChatMessageInline,]
    ordering = ['-updated_on']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display= ["id","user","is_online"]
    search_fields=["id","user__username"]
    list_per_page = 10
    list_display_links = list_display
    ordering = ['is_online']
