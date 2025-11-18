# Instagram Clone API

Bu loyiha Django va Django REST Framework yordamida yaratilgan Instagram klon API.

## Xususiyatlar
- Foydalanuvchi ro‘yxatdan o‘tish va autentifikatsiya
- Profil yaratish va yangilash
- Postlar, like va follow tizimi (keyinchalik qo‘shiladi)

## Texnologiyalar
- Python 3.13
- Django 5.x
- Django REST Framework

## O‘rnatish
```bash
git clone <repository_url>
cd instagaram_clone
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
