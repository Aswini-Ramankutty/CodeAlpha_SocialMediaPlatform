<<<<<<< HEAD
# SocialApp 🚀
A full-featured social media platform combining Instagram, WhatsApp, and Telegram.

## Quick Start (5 minutes)

### 1. Prerequisites
- Python 3.10+
- pip

### 2. Setup

```bash
# 1. Enter project folder
cd socialapp

# 2. Create virtual environment
python -m venv venv

# Activate it:
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py makemigrations core chat notifications
python manage.py migrate

# 5. Create a superuser (admin account)
python manage.py createsuperuser

# 6. Start the server
python manage.py runserver
```

### 3. Open in browser
Visit: **http://127.0.0.1:8000/**

For real-time chat (WebSockets), run with Daphne instead:
```bash
daphne -b 0.0.0.0 -p 8000 socialapp.asgi:application
```

## Features
- ✅ User registration, login, logout
- ✅ Instagram-style photo/video feed
- ✅ Stories (24-hour)
- ✅ Like, comment, save posts
- ✅ Follow/unfollow users
- ✅ Real-time chat (WebSockets via Django Channels)
- ✅ Group chats
- ✅ Typing indicators & read receipts
- ✅ Notifications system
- ✅ Search users, posts, hashtags
- ✅ Dark/Light mode
- ✅ Glassmorphism UI
- ✅ Mobile responsive

## Admin Panel
Visit: **http://127.0.0.1:8000/admin/**
Login with the superuser credentials you created.

## Project Structure
```
socialapp/
├── core/           # Main app: profiles, posts, feed
├── chat/           # Real-time messaging
├── notifications/  # Notification system
├── templates/      # All HTML templates
├── static/
│   ├── css/        # main.css, auth.css, landing.css
│   └── js/         # main.js, chat.js, feed.js
├── media/          # User uploads (auto-created)
├── manage.py
└── requirements.txt
```
=======
# CodeAlpha_SocialMediaPlatform
A modern full-stack social media platform built with Django, HTML, CSS, and JavaScript. It enables users to connect, share posts, interact with others, and manage profiles through a responsive and user-friendly interface.
>>>>>>> b871afe851593b8629e91de7d61ffe46b1df9d39
