"""Notifications views for SocialApp"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notifications_list(request):
    """List all notifications for the current user"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'sender__profile').order_by('-created_at')

    # Mark all as read
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications/notifications.html', {
        'notifications': notifications,
    })


@login_required
@require_POST
def mark_read(request, notif_id):
    """Mark a single notification as read"""
    Notification.objects.filter(
        id=notif_id, recipient=request.user
    ).update(is_read=True)
    return JsonResponse({'status': 'ok'})


@login_required
def notifications_api(request):
    """AJAX: Get recent unread notifications"""
    notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).select_related('sender', 'sender__profile').order_by('-created_at')[:10]

    data = [{
        'id': n.id,
        'type': n.notification_type,
        'sender': n.sender.username,
        'avatar': n.sender.profile.get_avatar_url(),
        'message': n.get_message(),
        'url': n.url,
        'created_at': n.created_at.isoformat(),
    } for n in notifications]
    return JsonResponse({'notifications': data, 'count': len(data)})
