# CodeAlpha_SocialMediaPlatform 🚀

A modern full-stack social media platform built with Django, HTML, CSS, and JavaScript. It enables users to connect, share posts, interact with others, and manage profiles through a responsive and user-friendly interface — combining the best of Instagram, WhatsApp, and Telegram.

## Quick Start (5 minutes)

### 1. Prerequisites
- Python 3.10+
- pip

### 2. Setup

```bash
cd socialapp
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations core chat notifications
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 3. Open in browser
Visit: **http://127.0.0.1:8000/**

## Features
- ✅ User registration, login, logout
- ✅ Instagram-style photo/video feed
- ✅ Like, comment, save posts
- ✅ Follow/unfollow users
- ✅ Real-time chat (WebSockets via Django Channels)
- ✅ Group chats
- ✅ Notifications system
- ✅ Search users, posts, hashtags
- ✅ Dark/Light mode
- ✅ Glassmorphism UI
- ✅ Mobile responsive

## Admin Panel
Visit: **http://127.0.0.1:8000/admin/**

## Project Structure
```
socialapp/
├── core/
├── chat/
├── notifications/
├── templates/
├── static/
├── manage.py
└── requirements.txt
```
