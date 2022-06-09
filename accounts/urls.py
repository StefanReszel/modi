from django.urls import path
from . import views


app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.UserCreateView.as_view(), name='sign_up'),
    path('reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('<username>/', views.AccountView.as_view(), name='account'),
    path('<username>/delete/', views.UserDeleteView.as_view(), name='account_delete'),
    path('<username>/edit-email/', views.UserEmailUpdateView.as_view(), name='account_email_update'),
    path('<username>/change-password/', views.PasswordChangeView.as_view(), name='password_change'),
]
