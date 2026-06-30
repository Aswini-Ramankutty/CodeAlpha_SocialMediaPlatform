
"""
Core views for SocialApp
Handles feed, profiles, posts, likes, follows, search
"""
 
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
 
from .models import UserProfile, Post, Comment, Like, Follow, Hashtag, SavedPost, Story
from .forms import RegisterForm, LoginForm, ProfileEditForm, PostCreateForm, CommentForm, ChangePasswordForm
from notifications.models import Notification
 
 
def landing_page(request):
    if request.user.is_authenticated:
        return redirect('feed')
    return render(request, 'core/landing.html')
 
 
def register_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('feed')
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})
 
 
def login_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_online = True
            profile.save()
            return redirect(request.GET.get('next', 'feed'))
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})
 
 
def logout_view(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            profile.is_online = False
            profile.last_seen = timezone.now()
            profile.save()
        except:
            pass
    logout(request)
    return redirect('login')
 
 
@login_required
def feed(request):
    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
 
    posts = Post.objects.filter(
        Q(author__in=following_ids) | Q(author=request.user),
        is_archived=False
    ).select_related('author', 'author__profile').order_by('-created_at')
 
    # Get liked post IDs as strings for template comparison
    liked_post_ids = list(
        Like.objects.filter(user=request.user, post__isnull=False)
        .values_list('post_id', flat=True)
    )
    liked_post_ids = [str(pid) for pid in liked_post_ids]
 
    # Get saved post IDs as strings
    saved_post_ids = list(
        SavedPost.objects.filter(user=request.user)
        .values_list('post_id', flat=True)
    )
    saved_post_ids = [str(pid) for pid in saved_post_ids]
 
    paginator = Paginator(posts, 10)
    page = request.GET.get('page', 1)
    posts_page = paginator.get_page(page)
 
    stories = Story.objects.filter(
        Q(author__in=following_ids) | Q(author=request.user),
        expires_at__gt=timezone.now()
    ).select_related('author', 'author__profile').order_by('-created_at')
 
    suggested = User.objects.exclude(
        Q(id__in=following_ids) | Q(id=request.user.id)
    ).select_related('profile').annotate(
        followers_count=Count('followers_set')
    ).order_by('-followers_count')[:5]
 
    trending_tags = Hashtag.objects.annotate(
        post_count=Count('posts')
    ).order_by('-post_count')[:8]
 
    context = {
        'posts': posts_page,
        'stories': stories,
        'suggested_users': suggested,
        'trending_tags': trending_tags,
        'post_form': PostCreateForm(),
        'liked_post_ids': liked_post_ids,
        'saved_post_ids': saved_post_ids,
    }
    return render(request, 'core/feed.html', context)
 
 
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if post.media:
                ext = post.media.name.split('.')[-1].lower()
                if ext in ['mp4', 'mov', 'avi', 'webm']:
                    post.media_type = 'video'
                else:
                    post.media_type = 'image'
            post.save()
            import re
            hashtags = re.findall(r'#(\w+)', post.caption)
            for tag in hashtags:
                ht, _ = Hashtag.objects.get_or_create(name=tag.lower())
                post.hashtags.add(ht)
            messages.success(request, 'Post shared!')
            return redirect('feed')
    return redirect('feed')
 
 
@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id, is_archived=False)
    comments = Comment.objects.filter(
        post=post, parent=None
    ).select_related('author', 'author__profile').prefetch_related(
        'replies', 'replies__author', 'replies__author__profile'
    )
    comment_form = CommentForm()
    is_liked = Like.objects.filter(user=request.user, post=post).exists()
    is_saved = SavedPost.objects.filter(user=request.user, post=post).exists()
 
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(Comment, id=parent_id)
            comment.save()
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post_id=str(post.id),
                    url=f'/post/{post.id}/'
                )
            return redirect('post_detail', post_id=post_id)
 
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'is_saved': is_saved,
    }
    return render(request, 'core/post_detail.html', context)
 
 
@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if post.author != request.user:
            Notification.objects.get_or_create(
                recipient=post.author,
                sender=request.user,
                notification_type='like',
                post_id=str(post.id),
                defaults={'url': f'/post/{post.id}/'}
            )
    return JsonResponse({'liked': liked, 'count': post.likes_count})
 
 
@login_required
@require_POST
def toggle_save(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    saved, created = SavedPost.objects.get_or_create(user=request.user, post=post)
    if not created:
        saved.delete()
        return JsonResponse({'saved': False})
    return JsonResponse({'saved': True})
 
 
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('profile', username=request.user.username)
 
 
@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    posts = Post.objects.filter(author=user, is_archived=False).order_by('-created_at')
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    is_own_profile = request.user == user
 
    context = {
        'profile_user': user,
        'profile': profile_obj,
        'posts': posts,
        'is_following': is_following,
        'is_own_profile': is_own_profile,
        'followers_count': profile_obj.followers_count,
        'following_count': profile_obj.following_count,
        'posts_count': posts.count(),
    }
    return render(request, 'core/profile.html', context)
 
 
@login_required
def edit_profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=profile_obj, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    return render(request, 'core/edit_profile.html', {'form': form})
 
 
@login_required
@require_POST
def toggle_follow(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow == request.user:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
 
    follow, created = Follow.objects.get_or_create(
        follower=request.user, following=user_to_follow
    )
    if not created:
        follow.delete()
        following = False
    else:
        following = True
        Notification.objects.get_or_create(
            recipient=user_to_follow,
            sender=request.user,
            notification_type='follow',
            defaults={'url': f'/profile/{request.user.username}/'}
        )
 
    followers_count = Follow.objects.filter(following=user_to_follow).count()
    return JsonResponse({'following': following, 'followers_count': followers_count})
 
 
@login_required
def followers_list(request, username):
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(
        following=user
    ).select_related('follower', 'follower__profile')
    return render(request, 'core/followers.html', {
        'profile_user': user, 'follows': followers, 'list_type': 'followers'
    })
 
 
@login_required
def following_list(request, username):
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        follower=user
    ).select_related('following', 'following__profile')
    return render(request, 'core/followers.html', {
        'profile_user': user, 'follows': following, 'list_type': 'following'
    })
 
 
@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    tab = request.GET.get('tab', 'users')
    users, posts, hashtags = [], [], []
 
    if query:
        if tab == 'users' or not tab:
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).select_related('profile').exclude(id=request.user.id)[:20]
        elif tab == 'posts':
            posts = Post.objects.filter(
                caption__icontains=query, is_archived=False
            ).select_related('author', 'author__profile')[:20]
        elif tab == 'hashtags':
            hashtags = Hashtag.objects.filter(
                name__icontains=query.lstrip('#')
            ).annotate(count=Count('posts')).order_by('-count')[:20]
 
    context = {
        'query': query, 'tab': tab,
        'users': users, 'posts': posts, 'hashtags': hashtags,
    }
    return render(request, 'core/search.html', context)
 
 
@login_required
def hashtag_posts(request, tag_name):
    tag = get_object_or_404(Hashtag, name=tag_name.lower())
    posts = Post.objects.filter(hashtags=tag, is_archived=False).order_by('-created_at')
    return render(request, 'core/hashtag.html', {'tag': tag, 'posts': posts})
 
 
@login_required
def settings_view(request):
    return render(request, 'core/settings.html')
 
 
@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=request.user.username,
                password=form.cleaned_data['current_password']
            )
            if user:
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed!')
                return redirect('settings')
            else:
                messages.error(request, 'Current password is incorrect.')
    else:
        form = ChangePasswordForm()
    return render(request, 'core/change_password.html', {'form': form})
 
 
@login_required
def explore(request):
    posts = Post.objects.filter(is_archived=False).annotate(
        like_count=Count('likes')
    ).order_by('-like_count', '-created_at')[:50]
    return render(request, 'core/explore.html', {'posts': posts})
 
