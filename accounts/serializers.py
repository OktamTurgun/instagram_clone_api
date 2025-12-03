import uuid
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserConfirmation
from .services import generate_confirmation, verify_code, resend_code

User = get_user_model()


# ===== REGISTER SERIALIZER =====
class RegisterSerializer(serializers.ModelSerializer):
    contact = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("contact", "password")

    def validate_contact(self, value):
        if "@" in value:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already registered")
        else:
            if User.objects.filter(phone_number=value).exists():
                raise serializers.ValidationError("Phone number already registered")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        return value

    def create(self, validated_data):
        contact = validated_data["contact"]
        password = validated_data["password"]
        temp_username = str(uuid.uuid4())[:12]
        auth_type = "email" if "@" in contact else "phone"

        user = User.objects.create_user(
            username=temp_username,
            email=contact if auth_type=="email" else None,
            phone_number=contact if auth_type=="phone" else None,
            password=password,
            auth_type=auth_type,
            auth_status="new"
        )

        generate_confirmation(user, f"{auth_type}_verification")
        return user

    def to_representation(self, instance):
        """New - Professional response"""
        contact = instance.email if instance.email else instance.phone_number
        contact_type = "email" if instance.email else "phone"
        
        return {
            "success": True,
            "message": f"Verification code sent to your {contact_type}",
            "data": {
                "user_id": str(instance.id),
                "contact": contact,
                "contact_type": contact_type,
                "auth_status": instance.auth_status,
                "next_step": {
                    "action": "verify",
                    "endpoint": "/api/auth/verify/",
                    "required_fields": ["contact", "code"]
                },
                "code_expires_in": "5 minutes"
            }
        }


# ===== VERIFY SERIALIZER =====
class VerifySerializer(serializers.Serializer):
    contact = serializers.CharField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        contact = data["contact"]
        code = data["code"]

        try:
            if "@" in contact:
                user = User.objects.get(email=contact.lower())
                ctype = "email_verification"
            else:
                user = User.objects.get(phone_number=contact)
                ctype = "phone_verification"
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        ok, msg = verify_code(user, ctype, code)
        if not ok:
            raise serializers.ValidationError(msg)

        user.auth_status = "code_verified"
        user.save()
        data["user"] = user
        return data

    def to_representation(self, instance):
        """New - Professional response with tokens"""
        user = self.context.get("user")
        
        if not user:
            # Fallback agar context bo'lmasa
            user = instance.get("user")
        
        refresh = RefreshToken.for_user(user)
        contact = user.email if user.email else user.phone_number
        
        return {
            "success": True,
            "message": "Verification successful! Please complete your profile.",
            "data": {
                "user": {
                    "id": str(user.id),
                    "contact": contact,
                    "username": user.username,
                    "auth_status": user.auth_status
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "token_type": "Bearer",
                    "expires_in": 3600
                },
                "next_step": {
                    "action": "complete_profile",
                    "endpoint": "/api/auth/complete-profile/",
                    "required_fields": ["username", "first_name", "last_name"],
                    "optional_fields": ["bio", "website", "location", "avatar"]
                }
            }
        }


# ===== RESEND SERIALIZER =====
class ResendSerializer(serializers.Serializer):
    contact = serializers.CharField()

    def validate(self, data):
        contact = data["contact"]
        try:
            if "@" in contact:
                user = User.objects.get(email=contact.lower())
                ctype = "email_verification"
            else:
                user = User.objects.get(phone_number=contact)
                ctype = "phone_verification"
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        resend_code(user, ctype)
        self.context['user'] = user
        return data

    def to_representation(self, instance):
        """ New - Professional resend response with tokens"""
        user = self.context.get('user')
        
        if not user:
            return {"success": True, "message": "Code sent"}
        
        contact = user.email if user.email else user.phone_number
        contact_type = "email" if user.email else "phone"
        
        return {
            "success": True,
            "message": f"New verification code sent to your {contact_type}",
            "data": {
                "contact": contact,
                "code_expires_in": "5 minutes",
                "next_step": {
                    "action": "verify",
                    "endpoint": "/api/auth/verify/"
                }
            }
        }


# ===== PROFILE COMPLETION SERIALIZER =====
class ProfileCompletionSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "bio",
            "website",
            "avatar",
            "location",
        )

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters")

        if not value.replace("_", "").isalnum():
            raise serializers.ValidationError(
                "Username may contain only letters, numbers and underscores"
            )

        user = self.instance
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This username is already taken")

        return value

    def update(self, user, validated_data):
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.username = validated_data.get("username", user.username)

        if not hasattr(user, 'profile'):
            from .models import Profile
            Profile.objects.create(user=user)

        profile = user.profile
        profile.bio = validated_data.get("bio", profile.bio)
        profile.website = validated_data.get("website", profile.website)
        profile.location = validated_data.get("location", profile.location)

        if "avatar" in validated_data:
            profile.avatar = validated_data["avatar"]

        profile.save()

        if user.auth_status != "completed":
            user.auth_status = "completed"
        user.save()

        return user

    def to_representation(self, instance):
        """ YANGI - Professional complete profile response"""
        return {
            "success": True,
            "message": "Profile completed successfully! You can now use all features.",
            "data": {
                "user": {
                    "id": str(instance.id),
                    "email": instance.email,
                    "phone_number": instance.phone_number,
                    "username": instance.username,
                    "first_name": instance.first_name,
                    "last_name": instance.last_name,
                    "full_name": instance.full_name,
                    "auth_status": instance.auth_status
                },
                "profile": {
                    "bio": instance.profile.bio if hasattr(instance, 'profile') else "",
                    "website": instance.profile.website if hasattr(instance, 'profile') else "",
                    "location": instance.profile.location if hasattr(instance, 'profile') else "",
                    "avatar": instance.profile.avatar.url if hasattr(instance, 'profile') and instance.profile.avatar else None,
                    "followers_count": instance.profile.followers_count if hasattr(instance, 'profile') else 0,
                    "following_count": instance.profile.following_count if hasattr(instance, 'profile') else 0
                }
            }
        }


# ===== LOGIN SERIALIZER =====
class LoginSerializer(serializers.Serializer):
    contact = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        contact = data.get("contact")
        password = data.get("password")

        try:
            if "@" in contact:
                user = User.objects.get(email=contact.lower())
            else:
                user = User.objects.get(phone_number=contact)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        if user.auth_status == "new":
            raise serializers.ValidationError({
                "error": "Verification required",
                "next_step": "verify",
                "endpoint": "/api/auth/verify/"
            })

        if user.auth_status == "code_verified":
            raise serializers.ValidationError({
                "error": "Profile not completed",
                "next_step": "complete_profile",
                "endpoint": "/api/auth/complete-profile/"
            })

        if user.auth_status != "completed":
            raise serializers.ValidationError("Account setup incomplete")

        data["user"] = user
        return data

    def to_representation(self, instance):
        """New - Professional login response with tokens and profile"""
        user = instance.get('user')
        refresh = RefreshToken.for_user(user)

        return {
            "success": True,
            "message": f"Welcome back, {user.username}!",
            "data": {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": user.full_name,
                    "auth_status": user.auth_status,
                    "auth_type": user.auth_type,
                    "user_role": user.user_role
                },
                "profile": {
                    "bio": user.profile.bio if hasattr(user, 'profile') else "",
                    "website": user.profile.website if hasattr(user, 'profile') else "",
                    "location": user.profile.location if hasattr(user, 'profile') else "",
                    "avatar": user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None,
                    "followers_count": user.profile.followers_count if hasattr(user, 'profile') else 0,
                    "following_count": user.profile.following_count if hasattr(user, 'profile') else 0
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            }
        }