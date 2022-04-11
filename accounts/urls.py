from django.urls import path
from . import views


app_name = 'accounts'

urlpatterns = [
    path('login/', views.ModiLoginView.as_view(), name='login'),
    path('logout/', views.ModiLogoutView.as_view(), name='logout'),
    path('register/', views.ModiUserCreateView.as_view(), name='sign_up'),
    path('reset/', views.ModiPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', views.ModiPasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('<username>/', views.AccountView.as_view(), name='account'),
    path('<username>/delete/', views.ModiUserDeleteView.as_view(), name='account_delete'),
    path('<username>/edit-email/', views.ModiUserEmailUpdateView.as_view(), name='account_email_update'),
    path('<username>/change-password/', views.ModiPasswordChangeView.as_view(), name='password_change'),
]
