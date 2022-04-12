from django import forms
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email

from .models import User
from .tasks import async_send_email


class UserCreationForm(auth_forms.UserCreationForm):
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control form-control-lg'
            }),
        )

    password2 = forms.CharField(
        label=_("Password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control form-control-lg'
            }),
       )

    class Meta:
        model = User
        fields = ("username", "email")
        field_classes = {'username': auth_forms.UsernameField}
        widgets = {
            'username': forms.TextInput(attrs={
                'autofocus': True,
                'class': 'form-control form-control-lg'
                }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'autocomplete': 'email',
            }),
        }


class AuthenticationForm(auth_forms.AuthenticationForm):
    username = auth_forms.UsernameField(
        label='Użytkownik lub email',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control form-control-lg'
            })
        )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'form-control form-control-lg'
            }),
        )


class UserEmailUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'autocomplete': 'email',
                }),
            }


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'autofocus': True,
            'class': 'form-control form-control-lg',
            }),
        )
    new_password1 = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control form-control-lg',
            }),
        )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control form-control-lg',
            }),
        )


class PasswordResetForm(auth_forms.PasswordResetForm):
    email = forms.CharField(
        label="Użytkownik lub email",
        max_length=254,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control form-control-lg',
            })
        )

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, *args, **kwargs):
        async_send_email.delay(
            subject_template_name, email_template_name, context, from_email, to_email)

    def get_users(self, email):
        """
        In addition to using `email`, this method makes
        possible to reset password by `username` as well.
        """
        try:
            validate_email(email)
            return super().get_users(email)
        except ValidationError:
            pass
        try:
            user = User.objects.get(username=email)
            if user.is_active and user.has_usable_password():
                return (user,)
        except User.DoesNotExist:
            return ()


class SetPasswordForm(auth_forms.SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control form-control-lg',
            }),
        )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control form-control-lg',
            }),
        )
