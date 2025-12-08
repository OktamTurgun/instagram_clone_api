from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, SimpleRateThrottle

class RegisterRateThrottle(AnonRateThrottle):
    """
    Rate limiting for registration endpoint.
    
    Prevents spam registrations.
    Limit: 3 attempts per hour per IP
    """
    rate = '3/hour'
    scope = 'register'


class VerifyRateThrottle(AnonRateThrottle):
    """
    Rate limiting for verification endpoint.
    
    Prevents brute force code guessing.
    Limit: 5 attempts per hour per IP
    """
    rate = '5/hour'
    scope = 'verify'


class ResendRateThrottle(AnonRateThrottle):
    """
    Rate limiting for resend code endpoint.
    
    Prevents code spam.
    Limit: 3 attempts per hour per IP
    """
    rate = '3/hour'
    scope = 'resend'


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limiting for login endpoint.
    
    Prevents brute force password attacks.
    Limit: 5 attempts per 5 minutes per IP
    """
    rate = '5/min'
    scope = 'login'


class ForgotPasswordRateThrottle(AnonRateThrottle):
    """
    Rate limiting for forgot password endpoint.
    
    Prevents password reset spam.
    Limit: 3 attempts per hour per IP
    """
    rate = '3/hour'
    scope = 'forgot_password'


class ResetPasswordRateThrottle(AnonRateThrottle):
    """
    Rate limiting for reset password endpoint.
    
    Prevents brute force code attacks.
    Limit: 5 attempts per hour per IP
    """
    rate = '5/hour'
    scope = 'reset_password'


class AuthenticatedUserThrottle(UserRateThrottle):
    """
    Rate limiting for authenticated users.
    
    More generous limits for logged-in users.
    Limit: 100 requests per hour
    """
    rate = '100/hour'
    scope = 'authenticated'


class BurstRateThrottle(AnonRateThrottle):
    """
    Short-term burst protection.
    
    Prevents rapid-fire requests.
    Limit: 10 requests per minute
    """
    rate = '10/min'
    scope = 'burst'


class SustainedRateThrottle(AnonRateThrottle):
    """
    Long-term sustained protection.
    
    Overall API protection.
    Limit: 1000 requests per day
    """
    rate = '1000/day'
    scope = 'sustained'

class ContactBasedRateThrottle(SimpleRateThrottle):
    """
    Rate limit based on contact (email/phone) instead of IP.
    
    More accurate for preventing abuse per account.
    """
    scope = 'contact'

    def get_cache_key(self, request, view):
        # Get contact from request data
        contact = request.data.get('contact', '')
        
        if not contact:
            return None  # No throttling if no contact
        
        # Normalize
        if '@' not in contact:
            try:
                from accounts.utils import validate_phone_number
                contact = validate_phone_number(contact, 'UZ')
            except:
                pass
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': contact.lower()
        }