"""URL patterns for SocialApp core app"""

from django.urls import path
from . import views

urlpatterns = [
    # Landing & Auth
    path('', views.landing_page, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Feed & Explore
    path('feed/', views.feed, name='feed'),
    path('explore/', views.explore, name='explore'),

    # Posts
    path('post/create/', views.create_post, name='create_post'),
    path('post/<uuid:post_id>/', views.post_detail, name='post_detail'),
    path('post/<uuid:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<uuid:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<uuid:post_id>/save/', views.toggle_save, name='toggle_save'),

    # Profiles
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('profile/<str:username>/followers/', views.followers_list, name='followers'),
    path('profile/<str:username>/following/', views.following_list, name='following'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    # Search
    path('search/', views.search, name='search'),
    path('hashtag/<str:tag_name>/', views.hashtag_posts, name='hashtag'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/password/', views.change_password, name='change_password'),
]
