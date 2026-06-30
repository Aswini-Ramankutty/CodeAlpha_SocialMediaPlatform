"""URL patterns for SocialApp chat"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('room/<uuid:room_id>/', views.chat_room, name='chat_room'),
    path('dm/<str:username>/', views.start_dm, name='start_dm'),
    path('group/create/', views.create_group, name='create_group'),
    path('api/messages/<uuid:room_id>/', views.get_messages_api, name='messages_api'),
]
