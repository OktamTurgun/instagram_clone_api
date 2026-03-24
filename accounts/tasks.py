from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email(self, user_email, code, contact_type='email'):
    """
    Verification code yuborish (email yoki SMS)
    
    Args:
        user_email: User email/phone
        code: 6-digit verification code
        contact_type: 'email' yoki 'phone'
    """
    try:
        if contact_type == 'email':
            subject = '📸 Instagram Clone - Email Verification'
            
            # HTML email
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; 
                        padding: 30px; 
                        text-align: center; 
                        border-radius: 10px 10px 0 0; 
                    }}
                    .content {{ 
                        background: #f9f9f9; 
                        padding: 30px; 
                        border-radius: 0 0 10px 10px; 
                    }}
                    .code {{ 
                        background: #667eea; 
                        color: white; 
                        font-size: 32px; 
                        font-weight: bold; 
                        padding: 20px; 
                        text-align: center; 
                        border-radius: 8px; 
                        letter-spacing: 8px; 
                        margin: 20px 0; 
                    }}
                    .footer {{ 
                        text-align: center; 
                        margin-top: 20px; 
                        color: #666; 
                        font-size: 12px; 
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📸 Instagram Clone</h1>
                        <p>Email Verification</p>
                    </div>
                    <div class="content">
                        <p>Hello!</p>
                        <p>Thank you for registering. Please use the following code to verify your email:</p>
                        <div class="code">{code}</div>
                        <p>This code will expire in <strong>5 minutes</strong>.</p>
                        <p>If you didn't create an account, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 Instagram Clone. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Instagram Clone - Email Verification
            
            Your verification code is: {code}
            
            This code will expire in 5 minutes.
            
            If you didn't create an account, please ignore this email.
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@instagram-clone.com'),
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f'✅ Verification email sent to {user_email}')
            return f'Email sent to {user_email}'
            
        else:
            # Phone/SMS (future implementation)
            logger.info(f'📱 SMS code for {user_email}: {code}')
            # TODO: Integrate SMS provider (Twilio, Eskiz.uz, etc.)
            return f'SMS sent to {user_email}'
        
    except Exception as exc:
        logger.error(f'❌ Error sending email to {user_email}: {str(exc)}')
        # Retry after 1 minute
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, user_email, reset_link):
    """
    Password reset email
    """
    try:
        subject = '🔐 Instagram Clone - Password Reset'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ 
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    color: white; 
                    padding: 30px; 
                    text-align: center; 
                    border-radius: 10px 10px 0 0; 
                }}
                .content {{ 
                    background: #f9f9f9; 
                    padding: 30px; 
                    border-radius: 0 0 10px 10px; 
                }}
                .button {{ 
                    display: inline-block; 
                    background: #f5576c; 
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                    font-weight: bold; 
                }}
                .footer {{ 
                    text-align: center; 
                    margin-top: 20px; 
                    color: #666; 
                    font-size: 12px; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset</h1>
                </div>
                <div class="content">
                    <p>Hello!</p>
                    <p>You requested to reset your password. Click the button below:</p>
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    <p>Or copy this link: <br><code>{reset_link}</code></p>
                    <p>This link will expire in <strong>1 hour</strong>.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2024 Instagram Clone. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Instagram Clone - Password Reset
        
        Click here to reset: {reset_link}
        
        This link will expire in 1 hour.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@instagram-clone.com'),
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f'✅ Password reset email sent to {user_email}')
        return f'Email sent to {user_email}'
        
    except Exception as exc:
        logger.error(f'❌ Error sending password reset to {user_email}: {str(exc)}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(user_email, username):
    """
    Welcome email after profile completion
    """
    subject = f'🎉 Welcome to Instagram Clone, {username}!'
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 30px; 
                text-align: center; 
                border-radius: 10px 10px 0 0; 
            }}
            .content {{ 
                background: #f9f9f9; 
                padding: 30px; 
                border-radius: 0 0 10px 10px; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Welcome, {username}!</h1>
            </div>
            <div class="content">
                <p>Thank you for joining Instagram Clone!</p>
                <p>Your account is now active and ready to use.</p>
                <p>Start exploring and sharing your moments! 📸</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_mail(
        subject=subject,
        message=f'Welcome {username}! Your account is now active.',
        from_email='noreply@instagram-clone.com',
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=True,
    )
    
    logger.info(f'Welcome email sent to {user_email}')