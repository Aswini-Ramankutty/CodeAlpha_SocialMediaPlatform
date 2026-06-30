"""
Django Channels WebSocket Consumer for real-time chat
Handles: connect, disconnect, send message, typing, read receipts
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for individual chat rooms"""

    async def connect(self):
        """Handle WebSocket connection"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        # Verify user has access to this room
        if not self.user.is_authenticated:
            await self.close()
            return

        has_access = await self.check_room_access()
        if not has_access:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Set user online
        await self.set_user_online(True)

        # Notify others this user is online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user': self.user.username,
                'status': 'online',
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.set_user_online(False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user': self.user.username,
                    'status': 'offline',
                    'last_seen': timezone.now().isoformat(),
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming messages from WebSocket"""
        data = json.loads(text_data)
        msg_type = data.get('type', 'message')

        if msg_type == 'message':
            # Save message to database and broadcast
            message = await self.save_message(data.get('content', ''), data.get('reply_to'))
            if message:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': str(message['id']),
                        'sender': self.user.username,
                        'avatar': message['avatar'],
                        'content': data.get('content', ''),
                        'created_at': message['created_at'],
                        'reply_to': data.get('reply_to'),
                        'reply_content': data.get('reply_content', ''),
                    }
                )

        elif msg_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user': self.user.username,
                    'is_typing': data.get('is_typing', False),
                }
            )

        elif msg_type == 'read':
            # Mark messages as read
            await self.mark_messages_read()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'user': self.user.username,
                }
            )

    # ── Event Handlers (called when group sends messages) ──

    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender': event['sender'],
            'avatar': event.get('avatar', ''),
            'content': event['content'],
            'created_at': event['created_at'],
            'is_own': event['sender'] == self.user.username,
            'reply_to': event.get('reply_to'),
            'reply_content': event.get('reply_content', ''),
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing'],
            }))

    async def read_receipt(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read',
            'user': event['user'],
        }))

    async def user_status(self, event):
        """Send user status update to WebSocket"""
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'status',
                'user': event['user'],
                'status': event['status'],
                'last_seen': event.get('last_seen', ''),
            }))

    # ── Database Operations (async) ──

    @database_sync_to_async
    def check_room_access(self):
        from .models import ChatRoom
        return ChatRoom.objects.filter(
            id=self.room_id, members=self.user
        ).exists()

    @database_sync_to_async
    def save_message(self, content, reply_to_id=None):
        from .models import ChatRoom, Message
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            reply_to = None
            if reply_to_id:
                try:
                    reply_to = Message.objects.get(id=reply_to_id)
                except Message.DoesNotExist:
                    pass

            msg = Message.objects.create(
                room=room,
                sender=self.user,
                content=content,
                reply_to=reply_to,
            )
            # Update room's updated_at
            room.updated_at = timezone.now()
            room.save(update_fields=['updated_at'])

            return {
                'id': str(msg.id),
                'avatar': self.user.profile.get_avatar_url(),
                'created_at': msg.created_at.isoformat(),
            }
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def mark_messages_read(self):
        from .models import ChatRoomMember
        ChatRoomMember.objects.filter(
            room_id=self.room_id, user=self.user
        ).update(last_read=timezone.now())

    @database_sync_to_async
    def set_user_online(self, is_online):
        from core.models import UserProfile
        UserProfile.objects.filter(user=self.user).update(
            is_online=is_online,
            last_seen=timezone.now()
        )
