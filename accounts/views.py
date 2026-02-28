from django.shortcuts import render
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView, exception_handler
from rest_framework.exceptions import Throttled

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser

# Import throttles
from .throttles import (
    RegisterRateThrottle,
    VerifyRateThrottle,
    ResendRateThrottle,
    LoginRateThrottle,
    ForgotPasswordRateThrottle,
    ResetPasswordRateThrottle,
)

from .serializers import (
    RegisterSerializer,
    VerifySerializer,
    ResendSerializer,
    ProfileCompletionSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


class RegisterView(GenericAPIView):
    """User registration - email yoki phone bilan"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ResetPasswordRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VerifyView(GenericAPIView):
    """Verification code tasdiqlash"""
    serializer_class = VerifySerializer
    permission_classes = [AllowAny]
    throttle_classes = [VerifyRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data.get("user")
        serializer.context['user'] = user
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResendView(GenericAPIView):
    """Verification code qayta yuborish"""
    serializer_class = ResendSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ResendRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
       
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileCompletionView(GenericAPIView):
    """User profilini to'ldirish"""
    serializer_class = ProfileCompletionSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class LoginView(GenericAPIView):
    """User login - email yoki phone bilan"""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ForgotPasswordView(GenericAPIView):
    """ Request password reset - send code to email/phone """

    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ForgotPasswordRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ResetPasswordView(GenericAPIView):
    """ Reset password with verification code """

    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ResetPasswordRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
def custom_exception_handler(exc, context):
    """
    Throttling (rate limit) xatolari uchun custom response qaytaradi.
    """
    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, Throttled):
        custom_response = {
            "success": False,
            "message": "Too many requests. Please try again later.",
            "data": {
                "error": "rate_limit_exceeded",
                "retry_after_seconds": exc.wait,
                "retry_after": f"{int(exc.wait // 60)} minutes" if exc.wait > 60 else f"{int(exc.wait)} seconds"
            }
        }
        response.data = custom_response

    return response

class ProfileUpdateView(RetrieveUpdateAPIView):
    """
    GET /api/auth/profile/    - Profile ko'rish
    PUT /api/auth/profile/    - Profile yangilash (avatar + bio + location + website)
    PATCH /api/auth/profile/  - Qisman yangilash
    
    MAVJUD ProfileCompletionSerializer ishlatiladi!
    """
    serializer_class = ProfileCompletionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_object(self):
        """Joriy user'ni qaytarish"""
        return self.request.user
    
class LogoutView(APIView):
    """
    POST /api/auth/logout/
    
    Logout user by blacklisting refresh token
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            
            if not refresh_token:
                return Response({
                    "success": False,
                    "message": "Refresh token is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                "success": True,
                "message": "Successfully logged out"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "message": "Invalid or expired token"
            }, status=status.HTTP_400_BAD_REQUEST)