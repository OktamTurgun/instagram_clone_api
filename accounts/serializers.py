from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserConfirmation
from .services import generate_confirmation, verify_code, resend_code

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "password")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            auth_type="email",
            auth_status="new"
        )

        # confirmation yuborish
        generate_confirmation(user, "email_verification")

        return user


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data["email"]
        code = data["code"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        ok, msg = verify_code(user, "email_verification", code)

        if not ok:
            raise serializers.ValidationError(msg)

        # email tasdiqlangan
        user.auth_status = "code_verified"
        user.save()

        return data



class ResendSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        email = data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        resend_code(user, "email_verification")

        return data

