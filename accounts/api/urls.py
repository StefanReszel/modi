from django.urls import path
from . import views


urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),  # POST
    path('login/', views.LoginView.as_view(), name='login'),  # GET, POST
    path('logout/', views.LogoutView.as_view(), name='logout'),  # POST
    path('password-reset/', views.PasswordResetView.as_view(), name='password-reset'),  # POST
    path('password-confirm/', views.PasswordConfirmView.as_view(), name='password-confirm'),  # POST
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),  # GET, DELETE, PUT, PATCH
]
