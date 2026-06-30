from django.contrib import admin
from .models import UserProfile, Post, Comment, Like, Follow, Hashtag, Story, SavedPost

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified', 'is_online', 'created_at']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'media_type', 'created_at', 'is_archived']
    list_filter = ['media_type', 'is_archived']

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']

admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Hashtag)
admin.site.register(Story)
admin.site.register(SavedPost)
