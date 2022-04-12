from django.test import TestCase
from django.urls import reverse

from accounts.tasks import async_send_email
from accounts.models import User
from accounts.forms import PasswordResetForm


class ViewsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

    def test_email_auth_backend(self):
        """
        Test of `accounts.backends.EmailAuthBackend`.
        """

        response = self.client.post(reverse("accounts:login"), data={"username": "test@email.com",
                                                                     "password": 'test1234',
                                                                     "next": reverse('dictionary:subject_list')})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:subject_list'))

        response = self.client.post(reverse("accounts:login"), data={"username": "non-existent@email.com",
                                                                     "password": 'test',
                                                                     "next": reverse('dictionary:subject_list')})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("accounts:login"), data={"username": "NonExistent",
                                                                     "password": '1234',
                                                                     "next": reverse('dictionary:subject_list')})
        self.assertEqual(response.status_code, 200)

    def test_raising_form_errors(self):
        """
        Test of `accounts.views.RaisingFormErrorsMixin`.
        """
        # incorrect data
        data = {
            "username": "AnotherUser",
            "email": "it will be invalid",
            "password1": "test1234",
            "password2": "1234test",
        }
        response = self.client.post(reverse("accounts:sign_up"), data=data)
        errors = dict(response.context['form'].errors)
        email_error = errors['email'][0]
        password_error = errors['password2'][0]

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, email_error)
        self.assertContains(response, password_error)
        self.assertEqual(User.objects.count(), 1)


class FormsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

    def test_modi_password_reset_form(self):
        """
        Test of `accounts.forms.PasswordResetForm.get_users`.
        """
        form = PasswordResetForm()

        users = form.get_users('test@email.com')
        self.assertIn(self.user, users)

        users = form.get_users('non-existent@email.com')
        self.assertNotIn(self.user, users)

        users = form.get_users('TestUser')
        self.assertIn(self.user, users)

        users = form.get_users('NonExistent')
        self.assertNotIn(self.user, users)


class TasksTestCase(TestCase):
    """
    Test of `accounts.tasks.async_send_email`.
    """
    def test_async_send_email(self):
        subject_template_name = 'accounts/modi/email/password_reset_subject.txt'
        email_template_name = 'accounts/modi/email/password_reset_email.html'
        from_email = 'MODi - My Own Dictionary'
        user_email = "user@example.com"
        context = {
                'email': user_email,
                'domain': "www.modi.pl",
                'site_name': "modi",
                'uid': 1,
                'user': "TestUser",
                'token': "1234-abcdeABCDE",
                'protocol': 'https',
            }

        result = async_send_email(subject_template_name, email_template_name, context, from_email, to_email=user_email)

        self.assertEqual(result, 1)
