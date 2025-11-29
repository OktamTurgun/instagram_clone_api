import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import UserConfirmation

def generate_confirmation(user, confirmation_type):
    """
    Create a new 6-digit confirmation code and invalidate previous unused codes.
    """
    # Old unused codes ni o'chirish
    UserConfirmation.objects.filter(
        user=user, confirmation_type=confirmation_type, is_used=False
    ).update(is_used=True)

    # 6 raqamli code
    code = str(uuid.uuid4().int)[:6].zfill(6)

    confirmation = UserConfirmation.objects.create(
        user=user,
        confirmation_type=confirmation_type,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=5)
    )

    # TODO: send via real email/SMS
    print(f"CONFIRMATION CODE for {user.email or user.phone_number}: {code}")

    return confirmation

def verify_code(user, confirmation_type, code):
    try:
        conf = UserConfirmation.objects.get(
            user=user, confirmation_type=confirmation_type, code=code, is_used=False
        )
    except UserConfirmation.DoesNotExist:
        return False, "Code is invalid"

    if conf.is_expired():
        return False, "Code expired"

    conf.is_used = True
    conf.save()
    return True, "Code verified"

def resend_code(user, confirmation_type):
    return generate_confirmation(user, confirmation_type)
