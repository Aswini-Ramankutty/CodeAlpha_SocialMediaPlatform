"""
Chat views for SocialApp WhatsApp/Telegram-style messaging
Handles room management and message display
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q

from .models import ChatRoom, ChatRoomMember, Message
from notifications.models import Notification
import json


@login_required
def chat_list(request):
    """List all chat rooms for the current user"""
    rooms = ChatRoom.objects.filter(
        members=request.user
    ).prefetch_related('members', 'members__profile').order_by('-updated_at')

    # Build room data with last message and unread count
    rooms_data = []
    for room in rooms:
        last_msg = room.get_last_message()
        unread = room.get_unread_count(request.user)
        other_member = None
        if room.room_type == 'direct':
            other_member = room.members.exclude(id=request.user.id).first()
        rooms_data.append({
            'room': room,
            'last_message': last_msg,
            'unread_count': unread,
            'other_member': other_member,
        })

    # Suggested users to start DM with
    from core.models import Follow
    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
    suggested = User.objects.filter(
        id__in=following_ids
    ).select_related('profile').exclude(
        id__in=ChatRoom.objects.filter(
            members=request.user, room_type='direct'
        ).values_list('members__id', flat=True)
    )[:5]

    return render(request, 'chat/chat_list.html', {
        'rooms_data': rooms_data,
        'suggested': suggested,
    })


@login_required
def start_dm(request, username):
    """Start or navigate to a direct message conversation"""
    other_user = get_object_or_404(User, username=username)
    if other_user == request.user:
        return redirect('chat_list')

    # Find existing DM room or create new one
    existing = ChatRoom.objects.filter(
        room_type='direct', members=request.user
    ).filter(members=other_user)

    if existing.exists():
        room = existing.first()
    else:
        room = ChatRoom.objects.create(room_type='direct', created_by=request.user)
        ChatRoomMember.objects.create(room=room, user=request.user, role='owner')
        ChatRoomMember.objects.create(room=room, user=other_user, role='member')

    return redirect('chat_room', room_id=room.id)


@login_required
def chat_room(request, room_id):
    """Individual chat room view"""
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    messages_qs = Message.objects.filter(room=room).select_related(
        'sender', 'sender__profile', 'reply_to', 'reply_to__sender'
    ).order_by('created_at')

    # Mark messages as read
    member = ChatRoomMember.objects.filter(room=room, user=request.user).first()
    if member:
        member.last_read = timezone.now()
        member.save()

    other_member = None
    if room.room_type == 'direct':
        other_member = room.members.exclude(id=request.user.id).first()

    return render(request, 'chat/chat_room.html', {
        'room': room,
        'messages': messages_qs,
        'other_member': other_member,
        'room_id': str(room.id),
    })


@login_required
def create_group(request):
    """Create a new group chat"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        members_ids = request.POST.getlist('members')
        if name and members_ids:
            room = ChatRoom.objects.create(
                name=name,
                room_type='group',
                created_by=request.user
            )
            # Add creator as owner
            ChatRoomMember.objects.create(room=room, user=request.user, role='owner')
            # Add members
            for uid in members_ids:
                try:
                    user = User.objects.get(id=uid)
                    ChatRoomMember.objects.get_or_create(
                        room=room, user=user, defaults={'role': 'member'}
                    )
                except User.DoesNotExist:
                    pass
            return redirect('chat_room', room_id=room.id)

    # Get following for member selection
    from core.models import Follow
    following = Follow.objects.filter(
        follower=request.user
    ).select_related('following', 'following__profile')
    return render(request, 'chat/create_group.html', {'following': following})


@login_required
def get_messages_api(request, room_id):
    """AJAX: Get messages for a room (for polling fallback)"""
    room = get_object_or_404(ChatRoom, id=room_id, members=request.user)
    after = request.GET.get('after')
    msgs = Message.objects.filter(room=room)
    if after:
        msgs = msgs.filter(created_at__gt=after)
    msgs = msgs.select_related('sender', 'sender__profile').order_by('created_at')

    data = [{
        'id': str(m.id),
        'sender': m.sender.username,
        'avatar': m.sender.profile.get_avatar_url(),
        'content': m.content if not m.is_deleted else 'This message was deleted',
        'message_type': m.message_type,
        'attachment': m.attachment.url if m.attachment else None,
        'is_own': m.sender == request.user,
        'created_at': m.created_at.isoformat(),
    } for m in msgs]
    return JsonResponse({'messages': data})
