from django.contrib.auth import password_validation


def password_validator(password):
    password_validation.validate_password(password)
