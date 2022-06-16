from rest_framework import serializers
from rest_framework.reverse import reverse_lazy

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from ..models import User
from .validators import password_validator
from ..tasks import async_send_email


class UserSerializer(serializers.ModelSerializer):
    subjects = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "subjects"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "password": {
                "write_only": True,
                "validators": [password_validator],
                "style": {"input_type": "password"},
            }
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        return user

    def get_subjects(self, obj):
        """
        Method returns url to user's list of subjects.

        https://www.django-rest-framework.org/api-guide/fields/#serializermethodfield
        """
        request = self.context.get("request")
        return reverse_lazy("subject-list", request=request)


class UserUpdateSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[password_validator],
        style={"input_type": "password"},
    )
    password_error_messages = {
        "password_incorrect": _(
            "Your old password was entered incorrectly. Please enter it again."
        ),
    }

    class Meta:
        model = User
        fields = ["email", "old_password", "new_password"]

    def validate_old_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError(
                self.password_error_messages["password_incorrect"]
            )
        return value

    def update(self, user, validated_data):
        user.email = validated_data.get("email", user.email)
        password = validated_data.get("new_password")
        if password:
            user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField()

    username_field = User._meta.get_field(User.USERNAME_FIELD)

    auth_error_messages = {
        "invalid_login": _(
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        "inactive": _("This account is inactive."),
    }

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username_or_email"], password=attrs["password"]
        )
        if not user:
            raise serializers.ValidationError(
                self.auth_error_messages["invalid_login"]
                % {"username": self.username_field.verbose_name}
            )
        if not user.is_active:
            raise serializers.ValidationError(self.auth_error_messages["inactive"])
        return {"user": user}


class PasswordResetSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()

    def send_mail(
        self, subject_template_name, email_template_name, context, from_email, to_email
    ):
        async_send_email.delay(
            subject_template_name, email_template_name, context, from_email, to_email
        )

    def save(
        self,
        request,
        subject_template_name,
        email_template_name,
        from_email,
        use_https,
        token_generator,
    ):

        user = self.get_user(self.validated_data["username_or_email"])

        if not user:
            return

        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain

        email_field_name = user.get_email_field_name()
        user_email = getattr(user, email_field_name)

        context = {
            "email": user_email,
            "domain": domain,
            "site_name": site_name,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            "token": token_generator.make_token(user),
            "protocol": "https" if use_https else "http",
        }
        self.send_mail(
            subject_template_name, email_template_name, context, from_email, user_email
        )

    def get_user(self, email):
        """
        In addition to using `email`, this method makes
        possible to reset password by `username` as well.
        """
        try:
            validate_email(email)
            try:
                user = User.objects.get(email=email)
                if user.is_active and user.has_usable_password():
                    return user
            except User.DoesNotExist:
                return
        except ValidationError:
            pass
        try:
            user = User.objects.get(username=email)
            if user.is_active and user.has_usable_password():
                return user
        except User.DoesNotExist:
            return


class PasswordConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True,
        validators=[password_validator],
        style={"input_type": "password"},
    )
    uid = serializers.CharField()
    token = serializers.CharField()

    def save(self, user, password):
        user.set_password(password)
        user.save()
