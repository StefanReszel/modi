from rest_framework import views, generics, status, permissions
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from ..models import User
from .authentication import LoginAuthentication
from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    PasswordConfirmSerializer,
)
from .permissions import IsMyAccountPermission


class AllowAnyMixin:
    permission_classes = [permissions.AllowAny]


class IsMyAccountMixin:
    permission_classes = [permissions.IsAuthenticated, IsMyAccountPermission]


class TokenGeneratorMixin:
    token_generator = default_token_generator


class RegisterView(AllowAnyMixin, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetailView(IsMyAccountMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_classes = {
        "retrieve": UserSerializer,
        "update": UserUpdateSerializer,
    }

    def get_serializer_class(self):
        self.serializer_class = (
            self.serializer_classes["retrieve"]
            if self.request.method == "GET"
            else self.serializer_classes["update"]
        )
        return self.serializer_class

    def perform_update(self, serializer):
        serializer.save()
        if "new_password" in self.request.data:
            update_session_auth_hash(self.request, self.get_object())


class LoginView(AllowAnyMixin, views.APIView):
    authentication_classes = [LoginAuthentication]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        return Response({"Cookie": "csrftoken"})

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)
            user_data = UserSerializer(user, context={"request": request}).data
            return Response(user_data)
        else:
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)


class LogoutView(IsMyAccountMixin, views.APIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({"status": "OK"})


class PasswordResetView(TokenGeneratorMixin, AllowAnyMixin, views.APIView):
    subject_template_name = "accounts/modi/email/password_reset_subject.txt"
    email_template_name = "accounts/modi/email/password_reset_email.html"
    from_email = "MODi - My Own Dictionary"

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            opts = {
                "request": self.request,
                "subject_template_name": self.subject_template_name,
                "email_template_name": self.email_template_name,
                "from_email": self.from_email,
                "use_https": self.request.is_secure(),
                "token_generator": self.token_generator,
            }
            serializer.save(**opts)
        return Response({"status": "OK"})


class PasswordConfirmView(TokenGeneratorMixin, AllowAnyMixin, views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = PasswordConfirmSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            user = self.get_user(data["uid"])
            token = data["token"]

            if user is not None:
                if self.token_generator.check_token(user, token):
                    serializer.save(user, data["new_password"])
                    return Response({"status": "OK"})
            return Response({"status": "invalid"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User._default_manager.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user
