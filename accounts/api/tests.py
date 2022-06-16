from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIRequestFactory, RequestsClient

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from accounts.models import User
from accounts.api.serializers import PasswordResetSerializer
from accounts.api.views import PasswordConfirmView


class LoginViewTestCase(APITestCase):
    client_class = RequestsClient

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

    def setUp(self):
        factory = APIRequestFactory()
        self.request = factory.request()

        self.login_url = reverse("login", request=self.request)

        response = self.client.get(self.login_url)

        self.csrftoken = response.cookies["csrftoken"]

    def test_login_without_passing_csrf_token_to_headers_should_return_status_403(self):
        response = self.client.post(
            self.login_url,
            data={"username_or_email": "TestUser", "password": "test1234"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_with_passing_csrf_token_to_headers_should_return_status_200(self):
        response = self.client.post(
            self.login_url,
            data={"username_or_email": "TestUser", "password": "test1234"},
            headers={"X-CSRFToken": self.csrftoken},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_passing_csrf_token_to_headers_but_providing_invalid_data_should_return_status_404(
        self,
    ):
        response = self.client.post(
            self.login_url,
            data={"username_or_email": "InvalidUser", "password": "test1234"},
            headers={"X-CSRFToken": self.csrftoken},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LogoutViewsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

    def setUp(self):
        factory = APIRequestFactory()
        self.request = factory.request()

        self.login_url = reverse("login", request=self.request)
        self.logout_url = reverse("logout", request=self.request)

        response_with_csrf_token_to_login = self.client.get(self.login_url)
        response = self.client.post(
            self.login_url,
            data={"username_or_email": "TestUser", "password": "test1234"},
            headers={
                "X-CSRFToken": response_with_csrf_token_to_login.cookies["csrftoken"]
            },
        )

        self.csrftoken = response.cookies["csrftoken"]

    def test_logout_should_return_status_200(self):
        response = self.client.post(
            self.logout_url, headers={"X-CSRFToken": self.csrftoken}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserDetailViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        cls.user_id = user.id

        another_user = User.objects.create_user(
            email="another-test@email.com",
            username="AnotherTestUser",
            password="test1234",
        )

        cls.another_user_id = another_user.id

    def setUp(self):
        self.client.login(username="TestUser", password="test1234")

        self.user = User.objects.get(id=self.user_id)
        self.another_user = User.objects.get(id=self.another_user_id)

    def test_http_get_method_by_logged_user_should_return_status_200(self):
        response = self.client.get(reverse("user-detail", args=[self.user_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_http_get_method_by_not_logged_user_should_return_status_403(self):
        response = self.client.get(reverse("user-detail", args=[self.another_user_id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_http_put_method_by_logged_user_should_return_status_200(self):
        response = self.client.put(
            reverse("user-detail", args=[self.user_id]),
            data={
                "email": "new-email@test.com",
                "old_password": "test1234",
                "new_password": "new-password",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_subsequent_to_http_put_method_user_object_should_have_new_email(self):
        old_email = self.user.email
        new_email = "new-email@test.com"

        self.client.put(
            reverse("user-detail", args=[self.user_id]),
            data={
                "email": new_email,
                "old_password": "test1234",
                "new_password": "new-password",
            },
        )
        user = User.objects.get(id=self.user_id)

        self.assertNotEqual(user, old_email)
        self.assertEqual(user.email, new_email)

    def test_subsequent_to_http_put_method_user_object_should_have_new_password(self):
        old_password = "test1234"
        new_password = "new-password"

        self.client.put(
            reverse("user-detail", args=[self.user_id]),
            data={
                "email": "new-email@test.com",
                "old_password": old_password,
                "new_password": new_password,
            },
        )
        user = User.objects.get(id=self.user_id)

        self.assertFalse(user.check_password(old_password))
        self.assertTrue(user.check_password(new_password))

    def test_http_patch_method_by_logged_user_should_return_status_200(self):
        response = self.client.patch(
            reverse("user-detail", args=[self.user_id]),
            data={"email": "test@email.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(
            reverse("user-detail", args=[self.user_id]),
            data={"old_password": "test1234", "new_password": "new-password"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PasswordResetSerializerTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

    def setUp(self):
        self.serializer = PasswordResetSerializer()

    def test_get_user_method_should_return_user_object_when_valid_email_provided(self):
        user = self.serializer.get_user("test@email.com")

        self.assertTrue(isinstance(user, User))

    def test_get_user_method_should_return_user_object_when_valid_username_provided(
        self,
    ):
        user = self.serializer.get_user("TestUser")

        self.assertTrue(isinstance(user, User))

    def test_get_user_method_should_return_none_when_invalid_email_provided(self):
        user = self.serializer.get_user("nonexistent@email.com")

        self.assertIsNone(user)

    def test_get_user_method_should_return_none_when_invalid_username_provided(self):
        user = self.serializer.get_user("NonexistentUser")

        self.assertIsNone(user)

    @patch("accounts.api.serializers.PasswordResetSerializer.send_mail")
    def test_save_method_should_invoke_send_mail_method(self, send_mail_mock):
        serializer = PasswordResetSerializer(
            data={"username_or_email": "test@email.com"}
        )

        serializer.is_valid(raise_exception=True)

        opts = {
            "request": Mock(),
            "subject_template_name": "example_subject_template_name",
            "email_template_name": "example_email_template_name",
            "from_email": "MODi - My Own Dictionary",
            "use_https": True,
            "token_generator": Mock(),
        }

        serializer.save(**opts)

        send_mail_mock.assert_called_once()


class PasswordResetViewTestCase(APITestCase):
    def test_when_http_post_method_view_should_return_status_200(self):
        response = self.client.post(
            reverse("password-reset"), data={"username_or_email": "test@email.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PasswordConfirmViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        cls.uid = urlsafe_base64_encode(force_bytes(cls.user.pk))

    def setUp(self):
        PasswordConfirmView.token_generator = Mock()

    def test_when_http_post_method_with_proper_view_should_return_status_200(self):
        response = self.client.post(
            reverse("password-confirm"),
            data={"new_password": "TopSecret", "uid": self.uid, "token": "abcde12345"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_when_http_post_method_with_invalid_uid_view_should_return_status_400(self):
        response = self.client.post(
            reverse("password-confirm"),
            data={"new_password": "TopSecret", "uid": "invalid", "token": "abcde12345"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_when_http_post_method_with_invalid_password_view_should_return_status_400(
        self,
    ):
        response = self.client.post(
            reverse("password-confirm"),
            data={"new_password": "top", "uid": self.uid, "token": "abcde12345"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
