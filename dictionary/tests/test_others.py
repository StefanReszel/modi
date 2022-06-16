"""
Tested modules:
    - `dictionary.words`
    - `dictionary.templatetags.modi_extras`
"""
from django.test import SimpleTestCase, TestCase, RequestFactory
from django.urls import reverse

from dictionary.templatetags.modi_extras import get_value
from dictionary.words import Words, DefinitionDoesNotExist, DuplicateError
from accounts.models import User
from dictionary.models import Subject, Dictionary


class WordsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )
        cls.subject = Subject.objects.create(title="Język angielski", owner=cls.user)
        cls.dictionary = Dictionary.objects.create(
            title="Podręcznik", description="Klasa I", subject=cls.subject
        )

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get(
            (
                reverse(
                    "dictionary:word_form",
                    args=[self.dictionary.subject.slug, self.dictionary.slug],
                )
            )
        )
        self.request.session = self.client.session
        self.words = Words(self.request, self.dictionary)

    def session_words(self) -> dict:
        """
        Helper function, returns dictionary with words from session.
        """
        return self.request.session[f"dictionary_{self.dictionary.id}"]

    def test_instantiating_word_class_should_add_dictionary_to_session(self):
        dictionary = Dictionary.objects.create(
            title="Książka", description="Klasa I", subject=self.subject
        )
        Words(self.request, dictionary)

        self.assertIn(f"dictionary_{dictionary.id}", self.request.session)

    def test_clear_session_should_make_session_empty(self):
        self.assertGreater(len(self.request.session.items()), 0)

        self.words.clear_session()

        self.assertEqual(len(self.request.session.items()), 0)

    def test_add_word_should_add_word_as_value_and_definition_as_key_to_session(self):
        self.words.add_word("love", "miłość")

        self.assertIn("miłość", self.session_words().keys())
        self.assertIn("love", self.session_words().values())
        self.assertEqual(self.session_words()["miłość"], "love")
        self.assertEqual(len(self.session_words()), 1)

    def test_add_word_should_raise_error_when_existing_definition_provided(self):
        self.words.add_word("love", "miłość")

        with self.assertRaises(DuplicateError):
            self.words.add_word("love", "miłość")

    def test_remove_word_should_delete_word_and_definition_from_session(self):
        self.words.add_word("love", "miłość")
        self.words.add_word("break", "przerwa")

        self.words.remove_word("miłość")

        self.assertNotIn("miłość", self.session_words().keys())
        self.assertNotIn("love", self.session_words().values())
        self.assertEqual(len(self.session_words()), 1)

    def test_remove_word_should_raise_error_if_definition_does_not_exist(self):
        with self.assertRaises(DefinitionDoesNotExist):
            self.words.remove_word("miłość")

    def test_get_words_should_return_list_of_tuples_sorted_by_values_which_are_words(
        self,
    ):
        self.words.add_word("break", "przerwa")
        self.words.add_word("code", "kodować")
        self.words.add_word("attention", "uwaga")

        expected_result = [
            ("uwaga", "attention"),
            ("przerwa", "break"),
            ("kodować", "code"),
        ]

        self.assertNotEqual(self.session_words().items(), dict(expected_result))
        self.assertListEqual(self.words.get_words(), expected_result)

    def test_clear_list_should_remove_all_words_and_definitions_from_session(self):
        self.words.add_word("break", "przerwa")
        self.words.add_word("code", "kodować")
        self.words.add_word("attention", "uwaga")

        self.assertEqual(len(self.session_words()), 3)

        self.words.clear_list()

        self.assertEqual(len(self.session_words()), 0)

    def test_save_to_db_after_saving_words_of_session_should_appear_in_the_words_of_dictionary_object(
        self,
    ):
        self.words.add_word("break", "przerwa")
        self.words.add_word("attention", "uwaga")

        self.words.save_to_db()

        self.assertEqual(len(self.dictionary.words), 2)

    def test_save_to_db_after_saving_dictionary_session_should_be_removed_from_session(
        self,
    ):
        self.words.add_word("break", "przerwa")
        self.words.add_word("attention", "uwaga")

        self.words.save_to_db()

        self.assertNotIn(f"dictionary_{self.dictionary.id}", self.request.session)

    def test_refresh_list_should_undo_changes_by_copying_words_from_dictionary_object_to_session(
        self,
    ):
        self.words.add_word("love", "miłość")
        self.words.save_to_db()

        self.words.refresh_list()

        self.assertEqual(self.session_words(), self.dictionary.words)


class TemplateFilterTestCase(SimpleTestCase):
    """
    Test of template filter `dictionary.templatetags.modi_extras.get_value`.
    """

    def setUp(self):
        self.sample_dictionary = {
            "key": "value",
        }

    def test_get_value_from_dict(self):
        result = get_value(self.sample_dictionary, "key")
        expected = "value"

        self.assertEqual(result, expected)
