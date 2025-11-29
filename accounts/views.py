from django.shortcuts import render
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import (
    RegisterSerializer,
    VerifySerializer,
    ResendSerializer,
    ProfileCompletionSerializer,
    LoginSerializer,
)

class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Verification code sent"}, status=status.HTTP_201_CREATED)


class VerifyView(GenericAPIView):
    serializer_class = VerifySerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get("user")

        # short-lived token yaratish
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # access tokenni qaytarish
        return Response({
            "message": "Email verified",
            "user_id": str(user.id),
            "access": access_token,
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)


class ResendView(GenericAPIView):
    serializer_class = ResendSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "New code sent"})

class ProfileCompletionView(GenericAPIView):
    serializer_class = ProfileCompletionSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Profile completed successfully"})

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone_number,
                "username": user.username
            }
        }, status=status.HTTP_200_OK)
    