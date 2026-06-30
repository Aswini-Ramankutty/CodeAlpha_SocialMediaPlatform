"""
Chat models for SocialApp real-time messaging
Supports direct messages and group chats (WhatsApp/Telegram style)
"""

from django.db import models
from django.contrib.auth.models import User
import uuid


class ChatRoom(models.Model):
    """Chat room for both direct and group messages"""
    ROOM_TYPES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True)  # For group chats
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='direct')
    members = models.ManyToManyField(User, through='ChatRoomMember', related_name='chat_rooms')
    avatar = models.ImageField(upload_to='chat/avatars/', blank=True, null=True)
    description = models.TextField(max_length=500, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.room_type == 'direct':
            members = self.members.all()
            return f"DM: {' & '.join(m.username for m in members)}"
        return f"Group: {self.name}"

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self, user):
        """Count unread messages for a specific user"""
        member = self.chatroommember_set.filter(user=user).first()
        if not member:
            return 0
        return self.messages.filter(created_at__gt=member.last_read).exclude(sender=user).count()


class ChatRoomMember(models.Model):
    """Through model for chat room membership with roles"""
    ROLES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('owner', 'Owner'),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default='member')
    last_read = models.DateTimeField(auto_now_add=True)
    is_muted = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.room}"


class Message(models.Model):
    """Individual message model with attachment support"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('audio', 'Audio'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    attachment = models.FileField(upload_to='chat/attachments/', blank=True, null=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, blank=True, related_name='read_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    @property
    def is_read_by_all(self):
        member_count = self.room.members.exclude(id=self.sender.id).count()
        return self.read_by.exclude(id=self.sender.id).count() >= member_count
