from django.contrib import admin
from .models import ChatRoom, ChatRoomMember, Message
admin.site.register(ChatRoom)
admin.site.register(ChatRoomMember)
admin.site.register(Message)
