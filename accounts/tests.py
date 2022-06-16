from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.tasks import async_send_email
from accounts.models import User
from accounts.forms import PasswordResetForm


class EmailAuthenticationTestCase(TestCase):
    """
    Test of `accounts.backends.EmailAuthBackend`.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

    def test_logging_with_valid_email_should_return_status_302(self):
        response = self.client.post(
            reverse("accounts:login"),
            data={
                "username": "test@email.com",
                "password": "test1234",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_logging_with_invalid_email_should_return_status_200(self):
        response = self.client.post(
            reverse("accounts:login"),
            data={
                "username": "non-existent@email.com",
                "password": "test",
                "next": reverse("dictionary:subject_list"),
            },
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("accounts:login"),
            data={"username": "NonExistent", "password": "1234"},
        )
        self.assertEqual(response.status_code, 200)


class RenderFormErrorsTestCase(TestCase):
    """
    Test of `accounts.views.RaisingFormErrorsMixin`.
    """

    def setUp(self):
        self.invalid_data = {
            "username": "AnotherUser",
            "email": "it will be invalid",
            "password1": "test1234",
            "password2": "1234test",
        }

    def test_raising_form_errors_response_should_return_status_200(self):
        response = self.client.post(reverse("accounts:sign_up"), data=self.invalid_data)

        self.assertEqual(response.status_code, 200)

    def test_raising_form_errors_response_should_contains_form_errors(self):
        response = self.client.post(reverse("accounts:sign_up"), data=self.invalid_data)

        errors = dict(response.context["form"].errors)

        email_error = errors["email"][0]
        password_error = errors["password2"][0]

        self.assertContains(response, email_error)
        self.assertContains(response, password_error)


class PasswordResetFormTestCase(TestCase):
    """
    Test of `accounts.forms.PasswordResetForm.get_users`.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

    def setUp(self):
        self.form = PasswordResetForm()

    @patch("django.contrib.auth.forms.PasswordResetForm.get_users")
    def test_method_get_users_of_form_should_invoke_parent_method_when_valid_email_provided(
        self, get_users_mock
    ):
        self.form.get_users("test@email.com")

        get_users_mock.assert_called()

    @patch("django.contrib.auth.forms.PasswordResetForm.get_users")
    def test_method_get_users_of_form_should_invoke_parent_method_when_invalid_email_provided(
        self, get_users_mock
    ):
        self.form.get_users("non-existent@email.com")

        get_users_mock.assert_called()

    def test_method_get_users_of_form_should_return_iterable_with_one_user_when_valid_username_provided(
        self,
    ):
        users = self.form.get_users("TestUser")

        self.assertIn(self.user, users)
        self.assertEqual(len(users), 1)

    def test_method_get_users_of_form_should_return_empty_iterable_when_invalid_username_provided(
        self,
    ):
        users = self.form.get_users("NonExistent")

        self.assertNotIn(self.user, users)
        self.assertEqual(len(users), 0)


class TasksTestCase(TestCase):
    """
    Test of `accounts.tasks.async_send_email`.
    """

    def setUp(self):
        self.subject_template_name = "accounts/modi/email/password_reset_subject.txt"
        self.email_template_name = "accounts/modi/email/password_reset_email.html"
        self.from_email = "MODi - My Own Dictionary"
        self.user_email = "user@example.com"
        self.context = {
            "email": self.user_email,
            "domain": "www.modi.pl",
            "site_name": "modi",
            "uid": 1,
            "user": "TestUser",
            "token": "1234-abcdeABCDE",
            "protocol": "https",
        }

    @patch("accounts.tasks.EmailMultiAlternatives.send")
    def test_async_send_email_should_invoke_send_method_of_email_multi_alternatives(
        self, send_mock
    ):

        async_send_email(
            self.subject_template_name,
            self.email_template_name,
            self.context,
            self.from_email,
            to_email=self.user_email,
        )

        send_mock.assert_called()
