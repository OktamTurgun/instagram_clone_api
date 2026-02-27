from django.urls import path
from .views import (
  LoginView,
  ProfileUpdateView, 
  RegisterView, 
  VerifyView, 
  ResendView, 
  ProfileCompletionView,
  ForgotPasswordView,
  ResetPasswordView,
)

urlpatterns = [
    # Registration flow
    # 1 Ro'yxatdan o'tish
    path("register/", RegisterView.as_view(), name='register'),

    # 2 Code tasdiqlash (email yoki phone)
    path("verify/", VerifyView.as_view(), name='verify'),

    # 3 Kodni qayta yuborish
    path("resend/", ResendView.as_view(), name='resend'),

    # 4 Profilni to'ldirish (username, avatar, bio va h.k.)
    path("complete-profile/", ProfileCompletionView.as_view(), name='complete-profile'),

    path('profile/', ProfileUpdateView.as_view(), name='profile'),

    # Authentication
    # 5 Login (email yoki phone + password)
    path("login/", LoginView.as_view(), name='login'),

    # Yangi - Password reset
    path("forgot-password/", ForgotPasswordView.as_view(), name='forgot-password'),
    path("reset-password/", ResetPasswordView.as_view(), name='reset-password'),

]