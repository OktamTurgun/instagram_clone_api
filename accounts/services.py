import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import UserConfirmation


def generate_confirmation(user, confirmation_type):
    """
    Yangi tasdiqlash kodini yaratadi.
    Avvalgi ishlatilmagan kodlar bo'lsa — ularni bekor qiladi.
    """
    # Eski active code'larni invalid qilish
    UserConfirmation.objects.filter(
        user=user,
        confirmation_type=confirmation_type,
        is_used=False
    ).update(is_used=True)

    confirmation = UserConfirmation.objects.create(
        user=user,
        confirmation_type=confirmation_type,
        expires_at=timezone.now() + timedelta(minutes=5),
        code=str(uuid.uuid4().int)[:6]
    )

    # Hozircha — kodni print qilamiz
    print(f"CONFIRMATION CODE for {user.email}: {confirmation.code}")

    return confirmation


def verify_code(user, confirmation_type, code):
    """
    Kodni tekshirish funksiyasi.
    """
    try:
        conf = UserConfirmation.objects.get(
            user=user,
            confirmation_type=confirmation_type,
            code=code,
            is_used=False
        )
    except UserConfirmation.DoesNotExist:
        return False, "Code is invalid"

    if conf.is_expired():
        return False, "Code expired"

    conf.is_used = True
    conf.save()

    return True, "Code verified"


def resend_code(user, confirmation_type):
    """ Eski kodni o'chirib, yangi kod yuboradi """
    return generate_confirmation(user, confirmation_type)
