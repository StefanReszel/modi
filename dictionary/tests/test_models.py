from django.test import TestCase
from accounts.models import User
from dictionary.models import Subject, Dictionary


class ModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(email='test@email.com',
                                        username='TestUser',
                                        password='test1234')
        cls.subject = Subject.objects.create(title='Język łaciński',
                                             owner=user)
        cls.dictionary = Dictionary.objects.create(subject=Subject.objects.first(),
                                                   title="słówka, powiedzonka i sentencje")

    def test_slugify_with_signal(self):
        """
        In the `dictionary.signals` there is a function `populate_slug`,
        which performs every time before `Model.save` is called.
        """
        self.assertEqual(self.subject.slug, 'jezyk-lacinski')
        self.subject.title = "Zażółć Gęślą Jaźń."
        self.subject.save()
        self.assertEqual(self.subject.slug, 'zazolc-gesla-jazn')

        self.assertEqual(self.dictionary.slug, 'slowka-powiedzonka-i-sentencje')
        self.dictionary.title = "Marek Aureliusz Rozmyślania."
        self.dictionary.save()
        self.assertEqual(self.dictionary.slug, 'marek-aureliusz-rozmyslania')

    def test_str(self):
        self.assertEqual(str(self.subject), self.subject.title)
        self.assertEqual(str(self.dictionary), self.dictionary.title)

    def test_get_absolute_url(self):
        self.assertEqual(self.subject.get_absolute_url(), f"/{self.subject.slug}/")
        self.assertEqual(self.dictionary.get_absolute_url(), f"/{self.subject.slug}/{self.dictionary.slug}/")
