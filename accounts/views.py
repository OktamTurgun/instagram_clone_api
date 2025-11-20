from django.shortcuts import render

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    RegisterSerializer,
    VerifySerializer,
    ResendSerializer
)


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Verification code sent"}, status=201)


class VerifyView(GenericAPIView):
    serializer_class = VerifySerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Email verified!"})


class ResendView(GenericAPIView):
    serializer_class = ResendSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "New code sent"})

