import uuid
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserConfirmation
from .services import generate_confirmation, verify_code, resend_code

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    contact = serializers.CharField(write_only=True)  # email yoki phone qabul qiladi
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("contact", "password")

    def validate_contact(self, value):
        # Email yoki phone ekanligini tekshirish
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

        # Auth type aniqlash
        auth_type = "email" if "@" in contact else "phone"

        user = User.objects.create_user(
            username=temp_username,
            email=contact if auth_type=="email" else None,
            phone_number=contact if auth_type=="phone" else None,
            password=password,
            auth_type=auth_type,
            auth_status="new"
        )

        # Confirmation code yuborish
        generate_confirmation(user, f"{auth_type}_verification")
        return user

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
        return data


class ProfileCompletionSerializer(serializers.ModelSerializer):
    # Profile modelidagi maydonlar
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

        # ✅ Current user'ni exclude qilish
        user = self.instance
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This username is already taken")

        return value

    def update(self, user, validated_data):
        # Userga tegishli bo'lgan maydonlar
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.username = validated_data.get("username", user.username)

        # ✅ Profile ma'lumotlari - hasattr bilan check qilamiz
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

        # User statusni o'zgartiramiz
        if user.auth_status != "completed":
            user.auth_status = "completed"
        user.save()

        return user


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
            raise serializers.ValidationError("User with this email does not exist")

        # check password
        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password")

        # check registration flow
        if user.auth_status == "new":
            raise serializers.ValidationError("Email is not verified")

        if user.auth_status == "code_verified":
            raise serializers.ValidationError("Profile is not completed")

        if user.auth_status != "completed":
            raise serializers.ValidationError("User is not fully registered")

        data["user"] = user
        return data