from unittest.mock import Mock

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIRequestFactory, RequestsClient

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from accounts.models import User
from accounts.api.serializers import PasswordResetSerializer
from accounts.api.views import PasswordConfirmView


class LoginAndLogoutViewsTestCase(APITestCase):
    """
    Add test for `LogoutView` ! ! !
    """
    client_class = RequestsClient

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

    def test_login(self):
        # Making URL for tests
        factory = APIRequestFactory()
        request = factory.request()
        url = reverse('login', request=request)

        # Obtaining a CSRF token.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        csrftoken = response.cookies['csrftoken']

        # Test without passing token to headers
        response = self.client.post(url, data={'username_or_email': 'TestUser', 'password': 'test1234'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Token passed to header
        response = self.client.post(url, data={'username_or_email': 'TestUser', 'password': 'test1234'},
                                    headers={'X-CSRFToken': csrftoken})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Obtaining a CSRF token.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        csrftoken = response.cookies['csrftoken']

        # With token in headers, but invalid data provided.
        response = self.client.post(url, data={'username_or_email': 'InvalidUser', 'password': 'test1234'},
                                    headers={'X-CSRFToken': csrftoken})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        # Logging in as above
        factory = APIRequestFactory()
        request = factory.request()
        url = reverse('login', request=request)

        response = self.client.get(url)
        csrftoken = response.cookies['csrftoken']

        response = self.client.post(url, data={'username_or_email': 'TestUser', 'password': 'test1234'},
                                    headers={'X-CSRFToken': csrftoken})

        # signing out
        url = reverse('logout', request=request)
        csrftoken = response.cookies['csrftoken']
        response = self.client.post(url, headers={'X-CSRFToken': csrftoken})

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserDetailViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

        cls.another_user = User.objects.create_user(email='another-test@email.com',
                                                    username='AnotherTestUser',
                                                    password='test1234')

    def setUp(self):
        self.client.login(username='TestUser', password='test1234')
    
    def test_get_method(self):
        # test getting data of logged user
        response = self.client.get(reverse('user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test getting data of another, not logged user
        response = self.client.get(reverse('user-detail', args=[self.another_user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # test updating user by diffrent methods
        response = self.client.put(reverse('user-detail', args=[self.user.id]),
                                   data={'email': 'new-email@test.com',
                                         'old_password': 'test1234',
                                         'new_password': 'new-password'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
       
        self.user = User.objects.get(id=self.user.id)
        self.assertEqual(self.user.email, 'new-email@test.com')
        self.assertTrue(self.user.check_password('new-password'))

        response = self.client.patch(reverse('user-detail', args=[self.user.id]),
                                   data={'email': 'test@email.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(reverse('user-detail', args=[self.user.id]),
                                   data={'old_password': 'new-password',
                                         'new_password': 'test1234'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(reverse('user-detail', args=[self.user.id]),
                                   data={'old_password': 'new-password',
                                         'new_password': 'test1234'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        PasswordResetSerializer.send_mail = Mock()

        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

    def test_get_user(self):
        """
        testing method of PasswordResetSerializer
        """
        serializer = PasswordResetSerializer()

        # getting user with e-mail
        user = serializer.get_user('test@email.com')
        self.assertTrue(isinstance(user, User))

        # getting user with username
        user = serializer.get_user('TestUser')
        self.assertTrue(isinstance(user, User))

        # getting user with invalid data
        user = serializer.get_user('NonexistentUser')
        self.assertIsNone(user)

        user = serializer.get_user('nonexistent@email.com')
        self.assertIsNone(user)

    def test_save(self):
        """
        testing method of PasswordResetSerializer
        """
        serializer = PasswordResetSerializer(data={'username_or_email': 'test@email.com'})

        serializer.is_valid(raise_exception=True)

        opts = {
                'request': Mock(),
                'subject_template_name': 'example_subject_template_name',
                'email_template_name': 'example_email_template_name',
                'from_email': 'MODi - My Own Dictionary',
                'use_https': True,
                'token_generator': Mock(),
            }

        serializer.save(**opts)

        serializer.send_mail.assert_called_once()

    def test_view(self):
        """
        test of PasswordResetView
        """
        response = self.client.post(reverse('password-reset'), data={'username_or_email': 'test@email.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PasswordConfirmViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

        cls.uid = urlsafe_base64_encode(force_bytes(cls.user.pk))

    def test_post(self):
        PasswordConfirmView.token_generator = Mock()

        response = self.client.post(reverse('password-confirm'), data={'new_password': 'TopSecret', 'uid': self.uid, 'token': 'abcde12345'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # case with invalid uid
        response = self.client.post(reverse('password-confirm'), data={'new_password': 'TopSecret', 'uid': 'invalid', 'token': 'abcde12345'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # case with invalid password
        response = self.client.post(reverse('password-confirm'), data={'new_password': 'top', 'uid': self.uid, 'token': 'abcde12345'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
