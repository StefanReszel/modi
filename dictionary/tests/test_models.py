from django.test import TestCase
from accounts.models import User
from dictionary.models import Subject, Dictionary


class SlugifyBySignalTestCase(TestCase):
    """
    In the `dictionary.signals` there is a function `populate_slug`,
    which performs every time before `Model.save` is called.
    """

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )
        cls.subject = Subject.objects.create(title="Język łaciński", owner=user)
        cls.dictionary = Dictionary.objects.create(
            subject=Subject.objects.first(), title="słówka, powiedzonka i sentencje"
        )

    def test_slug_of_created_subject_should_equals_expected_value(self):
        expected_value = "jezyk-lacinski"

        self.assertEqual(self.subject.slug, expected_value)

    def test_slug_of_updated_subject_should_equals_expected_value(self):
        self.subject.title = "Zażółć Gęślą Jaźń."
        self.subject.save()

        expected_value = "zazolc-gesla-jazn"

        self.assertEqual(self.subject.slug, expected_value)

    def test_slug_of_created_dictionary_should_equals_expected_value(self):
        expected_value = "slowka-powiedzonka-i-sentencje"
        self.assertEqual(self.dictionary.slug, expected_value)

    def test_slug_of_updated_dictionary_should_equals_expected_value(self):
        self.dictionary.title = "Marek Aureliusz Rozmyślania."
        self.dictionary.save()

        expected_value = "marek-aureliusz-rozmyslania"
        self.assertEqual(self.dictionary.slug, expected_value)


class CustomMethodsOfModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )
        cls.subject = Subject.objects.create(title="Język łaciński", owner=user)
        cls.dictionary = Dictionary.objects.create(
            subject=Subject.objects.first(), title="słówka, powiedzonka i sentencje"
        )

    def test_str_method_of_subject(self):
        self.assertEqual(str(self.subject), self.subject.title)

    def test_str_method_of_dictionary(self):
        self.assertEqual(str(self.dictionary), self.dictionary.title)

    def test_get_absolute_url_method_of_subject(self):
        self.assertEqual(self.subject.get_absolute_url(), f"/{self.subject.slug}/")

    def test_get_absolute_url_method_of_dictionary(self):
        self.assertEqual(
            self.dictionary.get_absolute_url(),
            f"/{self.subject.slug}/{self.dictionary.slug}/",
        )
