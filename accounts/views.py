from django.shortcuts import render
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled

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
        # to_representation ishlaydi
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VerifyView(GenericAPIView):
    """Verification code tasdiqlash"""
    serializer_class = VerifySerializer
    permission_classes = [AllowAny]
    throttle_classes = [VerifyRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # User'ni context'ga qo'shish
        user = serializer.validated_data.get("user")
        serializer.context['user'] = user
        
        # to_representation ishlaydi
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResendView(GenericAPIView):
    """Verification code qayta yuborish"""
    serializer_class = ResendSerializer
    permission_classes = [AllowAny]
    throttles_classes = [ResendRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # to_representation ishlaydi
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileCompletionView(GenericAPIView):
    """User profilini to'ldirish"""
    serializer_class = ProfileCompletionSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        # Authenticated user
        user = request.user
        
        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # to_representation ishlaydi
        return Response(serializer.data, status=status.HTTP_200_OK)


class LoginView(GenericAPIView):
    """User login - email yoki phone bilan"""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # to_representation ishlaydi
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
    
# Custom throttled response
def custom_exception_handler(exc, context):
    """Custom exception handler for better error messages"""
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