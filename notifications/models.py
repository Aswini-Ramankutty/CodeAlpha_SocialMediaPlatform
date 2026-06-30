"""
Notification models for SocialApp
Handles likes, comments, follows, and message notifications
"""

from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """Universal notification model for all notification types"""
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('reply', 'Reply'),
        ('follow', 'Follow'),
        ('message', 'Message'),
        ('mention', 'Mention'),
        ('post', 'Post'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    # Generic references (not all will be used for every type)
    post_id = models.CharField(max_length=100, blank=True, null=True)
    comment_id = models.IntegerField(blank=True, null=True)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.notification_type}"

    def get_message(self):
        """Generate human-readable notification message"""
        messages = {
            'like': f"{self.sender.username} liked your post",
            'comment': f"{self.sender.username} commented on your post",
            'reply': f"{self.sender.username} replied to your comment",
            'follow': f"{self.sender.username} started following you",
            'message': f"{self.sender.username} sent you a message",
            'mention': f"{self.sender.username} mentioned you",
            'post': f"{self.sender.username} shared a new post",
        }
        return self.message or messages.get(self.notification_type, "New notification")
