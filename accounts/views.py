from django.views.generic import CreateView, DeleteView, UpdateView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView,\
    PasswordChangeView, PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User
from .forms import ModiAuthenticationForm, ModiUserCreationForm, ModiUserEmailUpdateForm,\
    ModiPasswordChangeForm, ModiPasswordResetForm, ModiSetPasswordForm


class CommonLoginRequiredMixin(LoginRequiredMixin):
    login_url = '/accounts/login/'
    redirect_field_name = None


class GetUserMixin:
    def get_object(self):
        return self.request.user


class UpdateSuccessUrlMixin:
    def get_success_url(self):
        return reverse_lazy('accounts:account', args=[self.request.user.username])


class RaisingFormErrorsMixin:
    def form_invalid(self, form):
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(self.request, error)
        return super().form_invalid(form)


class SetSuccessMessagesMixin:
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


class AccountView(CommonLoginRequiredMixin, TemplateView):
    template_name = 'accounts/modi/account.html'


class ModiUserCreateView(RaisingFormErrorsMixin, SetSuccessMessagesMixin, CreateView):
    form_class = ModiUserCreationForm
    template_name = 'accounts/modi/sign_up.html'
    success_url = reverse_lazy('dictionary:subject_list')
    info_message = True

    def get_success_message(self):
        return "Pomyślnie zarejestrowano nowego użytkownika"


class ModiLoginView(RaisingFormErrorsMixin, SetSuccessMessagesMixin, LoginView):
    template_name = 'accounts/modi/login.html'
    authentication_form = ModiAuthenticationForm

    def get_success_message(self):
        return f"Witaj {self.request.user}!"


class ModiLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")

    def get_next_page(self):
        messages.success(self.request, "Wylogowano pomyślnie. Do zobaczenia!")
        return super().get_next_page()


class ModiUserDeleteView(CommonLoginRequiredMixin, GetUserMixin, DeleteView):
    model = User
    template_name = 'accounts/modi/account_delete.html'
    success_url = reverse_lazy('accounts:login')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Pomyślnie usunięto konto.")
        messages.info(request, "Pamiętaj, że możesz zarejestrować się ponownie.")
        return response


class ModiUserEmailUpdateView(CommonLoginRequiredMixin, SetSuccessMessagesMixin, RaisingFormErrorsMixin,
                              UpdateSuccessUrlMixin, GetUserMixin, UpdateView):
    model = User
    form_class = ModiUserEmailUpdateForm
    template_name = 'accounts/modi/user_email_update.html'

    def get_success_message(self):
        return "Pomyślnie zmieniono adres email."


class ModiPasswordChangeView(CommonLoginRequiredMixin, SetSuccessMessagesMixin, RaisingFormErrorsMixin,
                             UpdateSuccessUrlMixin, PasswordChangeView):
    form_class = ModiPasswordChangeForm
    template_name = 'accounts/modi/password_change_form.html'
    success_url = reverse_lazy('accounts:account')


class ModiPasswordResetView(SetSuccessMessagesMixin, PasswordResetView):
    form_class = ModiPasswordResetForm
    template_name = 'accounts/modi/password_reset_form.html'
    from_email = 'MODi - My Own Dictionary'
    subject_template_name = 'accounts/modi/email/password_reset_subject.txt'
    email_template_name = 'accounts/modi/email/password_reset_email.html'
    success_url = reverse_lazy('accounts:login')

    def get_success_message(self):
        return 'Sprawdź skrzynkę email.'


class ModiPasswordResetConfirmView(SetSuccessMessagesMixin, RaisingFormErrorsMixin, PasswordResetConfirmView):
    form_class = ModiSetPasswordForm
    template_name = 'accounts/modi/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:login')
    info_message = True
