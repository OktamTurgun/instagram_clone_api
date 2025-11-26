from django.urls import path
from .views import LoginView, RegisterView, VerifyView, ResendView, ProfileCompletionView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify/", VerifyView.as_view()),
    path("resend/", ResendView.as_view()),
    path("complete-profile/", ProfileCompletionView.as_view()),
    path("login/", LoginView.as_view()),
]