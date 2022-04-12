from django.views.generic import CreateView, DeleteView, UpdateView, TemplateView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import mixins

from .models import User
from .forms import AuthenticationForm, UserCreationForm, UserEmailUpdateForm,\
    PasswordChangeForm, PasswordResetForm, SetPasswordForm


class LoginRequiredMixin(mixins.LoginRequiredMixin):
    login_url = reverse_lazy('accounts:login')
    redirect_field_name = None


class GetUserMixin:
    def get_object(self):
        return self.request.user


class UpdateSuccessUrlMixin:
    def get_success_url(self):
        return reverse_lazy('accounts:account', args=[self.request.user.username])


class ErrorMessageMixin:
    def form_invalid(self, form):
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(self.request, error)
        return super().form_invalid(form)


class SuccessMessageMixin:
    info_message = False

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        if self.info_message:
            messages.info(self.request, self.get_info_message())
        return response

    def get_success_message(self):
        return "Pomyślnie zmieniono hasło."

    def get_info_message(self):
        return "Teraz możesz się zalogować."


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/modi/account.html'


class UserCreateView(ErrorMessageMixin, SuccessMessageMixin, CreateView):
    form_class = UserCreationForm
    template_name = 'accounts/modi/sign_up.html'
    success_url = reverse_lazy('dictionary:subject_list')
    info_message = True

    def get_success_message(self):
        return "Pomyślnie zarejestrowano nowego użytkownika"


class LoginView(ErrorMessageMixin, SuccessMessageMixin, auth_views.LoginView):
    template_name = 'accounts/modi/login.html'
    authentication_form = AuthenticationForm

    def get_success_message(self):
        return f"Witaj {self.request.user}!"


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("accounts:login")

    def get_next_page(self):
        messages.success(self.request, "Wylogowano pomyślnie. Do zobaczenia!")
        return super().get_next_page()


class UserDeleteView(LoginRequiredMixin, GetUserMixin, DeleteView):
    model = User
    template_name = 'accounts/modi/account_delete.html'
    success_url = reverse_lazy('accounts:login')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Pomyślnie usunięto konto.")
        messages.info(request, "Pamiętaj, że możesz zarejestrować się ponownie.")
        return response


class UserEmailUpdateView(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin,
                          UpdateSuccessUrlMixin, GetUserMixin, UpdateView):
    model = User
    form_class = UserEmailUpdateForm
    template_name = 'accounts/modi/user_email_update.html'

    def get_success_message(self):
        return "Pomyślnie zmieniono adres email."


class PasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin,
                         UpdateSuccessUrlMixin, auth_views.PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'accounts/modi/password_change_form.html'
    success_url = reverse_lazy('accounts:account')


class PasswordResetView(SuccessMessageMixin, auth_views.PasswordResetView):
    form_class = PasswordResetForm
    template_name = 'accounts/modi/password_reset_form.html'
    from_email = 'MODi - My Own Dictionary'
    subject_template_name = 'accounts/modi/email/password_reset_subject.txt'
    email_template_name = 'accounts/modi/email/password_reset_email.html'
    success_url = reverse_lazy('accounts:login')

    def get_success_message(self):
        return 'Sprawdź skrzynkę email.'


class PasswordResetConfirmView(SuccessMessageMixin, ErrorMessageMixin,
                               auth_views.PasswordResetConfirmView):
    form_class = SetPasswordForm
    template_name = 'accounts/modi/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:login')
    info_message = True
