from django.urls import path
from .views import RegisterView, VerifyView, ResendView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify/", VerifyView.as_view()),
    path("resend/", ResendView.as_view()),
]