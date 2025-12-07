import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import UserConfirmation

def generate_confirmation(user, confirmation_type):
    """
    Create confirmation code and send email/SMS
    """
    # Old codes ni invalid qilish
    UserConfirmation.objects.filter(
        user=user, 
        confirmation_type=confirmation_type, 
        is_used=False
    ).update(is_used=True)

    # 6-digit code
    code = str(uuid.uuid4().int)[:6].zfill(6)

    confirmation = UserConfirmation.objects.create(
        user=user,
        confirmation_type=confirmation_type,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=5)
    )

    # Task selection based on type
    from .tasks import send_verification_email, send_password_reset_email
    
    contact = user.email if user.email else user.phone_number
    contact_type = 'email' if user.email else 'phone'
    
    if confirmation_type == 'password_reset':
        # Password reset email with link
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?token={confirmation.token}"
        
        send_password_reset_email.delay(contact, reset_link)
        print(f" PASSWORD RESET CODE for {contact}: {code}")
        print(f" RESET LINK: {reset_link}")
    else:
        # Verification email
        send_verification_email.delay(contact, code, contact_type)
        print(f" CONFIRMATION CODE for {contact}: {code}")

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
