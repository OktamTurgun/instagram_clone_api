# Instagram Clone - Backend API

Full-featured Django REST Framework backend for Instagram-like social media application with enterprise-grade authentication, async task processing, and comprehensive security.

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.x-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

##  Features

###  Implemented (Week 1)

#### Authentication System
- 🔐 **Dual Channel Authentication** - Email or Phone number registration
- 📧 **Email Verification** - 6-digit code with 5-minute expiry
- 📱 **Phone Validation** - International format support (Google libphonenumber)
- 🔄 **Multi-step Registration** - Register → Verify → Complete Profile → Login
- 🔑 **JWT Authentication** - Access + Refresh tokens
- 🔒 **Password Reset** - Secure reset with verification codes
- ⏱️ **Rate Limiting** - API abuse prevention

#### Technical Infrastructure
- ⚡ **Async Email** - Celery + Redis for background task processing
- 🎨 **Professional API** - Consistent response format with next-step guidance
- 🛡️ **Security** - Rate limiting, password hashing, code expiry
- 🌍 **International Support** - Phone number validation for 200+ countries
- 📊 **Scalable Architecture** - Ready for production deployment

### 🔜 Coming Soon (Week 2-4)

- [ ] Follow/Unfollow system
- [ ] User search and suggestions
- [ ] Profile editing with avatar upload
- [ ] Posts with multiple images
- [ ] Comments and likes
- [ ] Real-time notifications (WebSocket)
- [ ] Direct messaging
- [ ] Stories (24h expiry)

##  Architecture
```
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐
│   Django API    │◄────►│    Redis     │◄────►│   Celery    │
│   (REST Views)  │      │  (Broker)    │      │  (Workers)  │
└─────────────────┘      └──────────────┘      └─────────────┘
         │                                             │
         │                                             ▼
         ▼                                      ┌─────────────┐
┌─────────────────┐                           │ Email/SMS   │
│   PostgreSQL    │                           │  Service    │
│   (Database)    │                           └─────────────┘
└─────────────────┘
```

##  Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL 14+
- Redis 7+ (or Memurai for Windows)
- Git

### Installation
```bash
# 1. Clone repository
git clone https://github.com/yourusername/instagram_clone.git
cd instagram_clone

# 2. Create virtual environment
pipenv install
# or
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pipenv install
# or
pip install -r requirements.txt

# 4. Environment variables
cp .env.example .env
# Edit .env with your configuration:
# - DATABASE_URL
# - SECRET_KEY
# - REDIS_URL
# - EMAIL_HOST_USER (optional)
# - EMAIL_HOST_PASSWORD (optional)

# 5. Database setup
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Start Redis
# Windows (Memurai): Start from Start Menu
# Linux/Mac: redis-server
# WSL: sudo service redis-server start

# 8. Start Celery worker (new terminal)
celery -A config worker --loglevel=info --pool=solo

# 9. Start Django server
python manage.py runserver
```

### Quick Test
```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"contact":"test@example.com","password":"secure123"}'

# Check console for verification code
# Verify email
curl -X POST http://localhost:8000/api/auth/verify/ \
  -H "Content-Type: application/json" \
  -d '{"contact":"test@example.com","code":"123456"}'
```

##  API Documentation

### Base URL
```
Development: http://localhost:8000/api/
Production: https://your-domain.com/api/
```

### Authentication Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register/` | POST | No | Register new user (email or phone) |
| `/auth/verify/` | POST | No | Verify email/phone with code |
| `/auth/resend/` | POST | No | Resend verification code |
| `/auth/complete-profile/` | PUT | Yes | Complete user profile |
| `/auth/login/` | POST | No | Login and get JWT tokens |
| `/auth/forgot-password/` | POST | No | Request password reset code |
| `/auth/reset-password/` | POST | No | Reset password with code |

### Request/Response Examples

<details>
<summary><b>POST /api/auth/register/</b> - Register User</summary>

**Request:**
```json
{
  "contact": "user@example.com",
  "password": "securePassword123"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Verification code sent to your email",
  "data": {
    "user_id": "uuid-here",
    "contact": "user@example.com",
    "contact_type": "email",
    "auth_status": "new",
    "next_step": {
      "action": "verify",
      "endpoint": "/api/auth/verify/",
      "required_fields": ["contact", "code"]
    },
    "code_expires_in": "5 minutes"
  }
}
```
</details>

<details>
<summary><b>POST /api/auth/verify/</b> - Verify Email/Phone</summary>

**Request:**
```json
{
  "contact": "user@example.com",
  "code": "123456"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Verification successful! Please complete your profile.",
  "data": {
    "user": {
      "id": "uuid",
      "contact": "user@example.com",
      "auth_status": "code_verified"
    },
    "tokens": {
      "access": "eyJhbGc...",
      "refresh": "eyJhbGc...",
      "token_type": "Bearer",
      "expires_in": 3600
    },
    "next_step": {
      "action": "complete_profile",
      "endpoint": "/api/auth/complete-profile/"
    }
  }
}
```
</details>

<details>
<summary><b>POST /api/auth/login/</b> - Login</summary>

**Request:**
```json
{
  "contact": "user@example.com",
  "password": "securePassword123"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Welcome back, username!",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "username": "username",
      "full_name": "John Doe"
    },
    "profile": {
      "bio": "Hello World",
      "avatar": "/media/avatars/avatar.jpg",
      "followers_count": 0,
      "following_count": 0
    },
    "tokens": {
      "access": "eyJhbGc...",
      "refresh": "eyJhbGc...",
      "expires_in": 3600
    }
  }
}
```
</details>

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Register | 3 requests | per hour |
| Login | 10 requests | per minute |
| Verify | 5 requests | per hour |
| Resend | 3 requests | per hour |
| Forgot Password | 3 requests | per hour |
| Reset Password | 5 requests | per hour |

**Rate Limit Response:** `429 Too Many Requests`
```json
{
  "detail": "Request was throttled. Expected available in 3599 seconds."
}
```

##  Security

### Implemented Security Features

- ✅ **Password Hashing** - PBKDF2 algorithm with salt
- ✅ **JWT Tokens** - Secure access and refresh token system
- ✅ **Rate Limiting** - Per-endpoint throttling to prevent abuse
- ✅ **Code Expiry** - Verification codes expire after 5 minutes
- ✅ **Input Validation** - Comprehensive serializer validation
- ✅ **SQL Injection Protection** - Django ORM parameterized queries
- ✅ **XSS Protection** - DRF JSON responses
- ✅ **CSRF Protection** - Token-based for state-changing operations

### Security Best Practices
```python
# Environment Variables (never commit)
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0

# Production Settings
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## 🧪 Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts

# Coverage report
coverage run --source='.' manage.py test
coverage report
coverage html
```

##  Project Structure
```
instagram_clone/
├── accounts/                 # User authentication app
│   ├── models.py            # User, Profile, UserConfirmation
│   ├── serializers.py       # API serializers
│   ├── views.py             # API views
│   ├── urls.py              # URL routing
│   ├── tasks.py             # Celery tasks (email)
│   ├── throttles.py         # Rate limiting
│   ├── utils.py             # Phone validation utilities
│   └── signals.py           # Profile auto-creation
│
├── config/                   # Project configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # Root URL configuration
│   ├── celery.py            # Celery configuration
│   └── wsgi.py              # WSGI application
│
├── shared/                   # Shared utilities
│   └── models.py            # BaseModel (UUID, timestamps)
│
├── media/                    # User uploaded files
│   └── avatars/             # Profile avatars
│
├── .env                      # Environment variables (not in git)
├── .gitignore               # Git ignore rules
├── Pipfile                  # Python dependencies
├── manage.py                # Django management script
└── README.md                # This file
```

##  Tech Stack

### Backend
- **Django 5.x** - Web framework
- **Django REST Framework 3.x** - API framework
- **PostgreSQL 14+** - Primary database
- **Redis 7+** - Message broker & cache
- **Celery 5.x** - Async task queue

### Libraries
- **djangorestframework-simplejwt** - JWT authentication
- **phonenumbers** - International phone validation
- **Pillow** - Image processing
- **django-celery-beat** - Periodic tasks
- **django-celery-results** - Task result storage

### Development Tools
- **Pipenv** - Dependency management
- **Git** - Version control
- **Postman** - API testing

##  Performance

### Response Times (avg)
- **Registration:** ~100ms (instant, email async)
- **Login:** ~150ms
- **Verification:** ~120ms
- **Profile Update:** ~80ms

### Scalability
- **Async Processing:** Celery handles 100+ concurrent tasks
- **Rate Limiting:** Prevents API abuse
- **Database Indexing:** Optimized queries
- **Caching Ready:** Redis integration

##  Troubleshooting

### Common Issues

<details>
<summary><b>Redis Connection Error</b></summary>

**Error:** `ConnectionRefusedError: [WinError 10061]`

**Solution:**
```bash
# Windows (Memurai)
Start → Memurai → Start Server

# WSL/Linux
sudo service redis-server start
redis-cli ping  # Should return PONG
```
</details>

<details>
<summary><b>Celery Worker Not Starting</b></summary>

**Error:** `[Errno 10061] No connection could be made`

**Solution:**
1. Ensure Redis is running
2. Check CELERY_BROKER_URL in settings
3. Use `--pool=solo` on Windows:
```bash
celery -A config worker --loglevel=info --pool=solo
```
</details>

<details>
<summary><b>Migration Errors</b></summary>

**Solution:**
```bash
# Reset migrations (development only!)
python manage.py migrate accounts zero
python manage.py migrate

# Fresh start
rm db.sqlite3
rm -rf accounts/migrations/
python manage.py makemigrations
python manage.py migrate
```
</details>

##  Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use production database (PostgreSQL)
- [ ] Set up Redis (persistent)
- [ ] Configure email backend (SMTP)
- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Configure static files (S3/CDN)
- [ ] Set up Celery worker service
- [ ] Configure logging
- [ ] Set up monitoring (Sentry)
- [ ] Database backups

### Deployment Options

- **Heroku** - Quick deployment with add-ons
- **DigitalOean** - VPS with full control
- **AWS** - Elastic Beanstalk or EC2
- **Docker** - Containerized deployment

##  Roadmap

### Week 1 (Completed) 
- [x] Authentication system
- [x] Async email with Celery
- [x] Phone validation
- [x] Password reset
- [x] Rate limiting

### Week 2 (In Progress) 
- [ ] Follow/Unfollow system
- [ ] User search
- [ ] Profile editing
- [ ] Avatar upload

### Week 3 (Planned) 
- [ ] Posts with images
- [ ] Comments
- [ ] Likes
- [ ] Feed algorithm

### Week 4 (Planned) 
- [ ] Real-time notifications
- [ ] Direct messaging
- [ ] Stories
- [ ] Hashtags

##  Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Author

**Uktam Turgunov**
- GitHub: [@uktamturgun](https://github.com/uktamturgun)
- LinkedIn: [Uktam Turgunov](https://linkedin.com/in/uktamturgunov)
- Email: uktamturgunov30@gmail.com

##  Acknowledgments

- Django REST Framework documentation
- Celery documentation
- Google libphonenumber
- Instagram for inspiration

##  Support

For support, email uktamturgunov30@gmail.com or open an issue on GitHub.

---

⭐ **Star this repo** if you find it helpful!

**Built with ❤️ using Django & DRF**