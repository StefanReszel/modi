"""
Tested modules:
    - `dictionary.words`
    - `dictionary.templatetags.modi_extras`
"""
from django.test import SimpleTestCase, TestCase, RequestFactory
from django.urls import reverse

from dictionary.templatetags.modi_extras import get_value
from dictionary.words import Words , DefinitionDoesNotExist, DuplicateError
from accounts.models import User
from dictionary.models import Subject, Dictionary


class WordsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user=User.objects.create_user(email='test@email.com',
                                           username='TestUser',
                                           password='test1234')
        cls.subject = Subject.objects.create(title='Język angielski',
                                              owner=cls.user)
        cls.dictionary = Dictionary.objects.create(title='Podręcznik',
                                                   description='Klasa I',
                                                   subject=cls.subject)

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get((reverse('dictionary:word_form',
                                                 args=[self.dictionary.subject.slug, self.dictionary.slug])))
        self.request.session = self.client.session
        self.words = Words(self.request, self.dictionary)

    def session_words(self) -> dict:
        """
        Helper function, returns dictionary with words from session.
        """
        return self.request.session[f"dictionary_{self.dictionary.id}"]

    def test_instantiating_and_clear_session(self):
        dictionary = Dictionary.objects.create(title='Książka',
                                                    description='Klasa I',
                                                    subject=self.subject)
        words = Words(self.request, dictionary)

        self.assertIn(f"dictionary_{self.dictionary.id}", self.request.session)
        self.assertIn(f"dictionary_{dictionary.id}", self.request.session)

        words.clear_session()

        self.assertIn(f"dictionary_{self.dictionary.id}", self.request.session)
        self.assertNotIn(f"dictionary_{dictionary.id}", self.request.session)

        self.words.clear_session()

        self.assertNotIn(f"dictionary_{self.dictionary.id}", self.request.session)   

    def test_add_word_and_remove_word(self):
        # `Words.add_word`
        self.words.add_word('love', 'miłość')
        self.words.add_word('war', 'wojna')
        self.words.add_word('angel', 'anioł')

        self.assertIn('miłość', self.session_words())
        self.assertEqual(self.session_words()['miłość'], 'love')

        self.assertIn('wojna', self.session_words())
        self.assertEqual(self.session_words()['wojna'], 'war')

        self.assertIn('anioł', self.session_words())
        self.assertEqual(self.session_words()['anioł'], 'angel')
        
        with self.assertRaises(DuplicateError):
            self.words.add_word('love', 'miłość')

        # `Words.remove_word`
        self.assertEqual(len(self.session_words()), 3)
        
        self.words.remove_word('miłość')
        self.assertEqual(len(self.session_words()), 2)

        with self.assertRaises(DefinitionDoesNotExist):
            self.words.remove_word('miłość')

        with self.assertRaises(DefinitionDoesNotExist):
            self.words.remove_word('war')

        with self.assertRaises(DefinitionDoesNotExist):
            self.words.remove_word('diabeł')

        self.words.remove_word('wojna')
        self.assertEqual(len(self.session_words()), 1)

    def test_get_words(self):
        """
        `Words.get_words` sorts dictionary from session
        according to words and returns list of tuples.
        """
        self.words.add_word('break', 'przerwa')
        self.words.add_word('code', 'kodować')
        self.words.add_word('attention', 'uwaga')

        expected_result = [('uwaga', 'attention'), ('przerwa', 'break'), ('kodować', 'code')]

        self.assertNotEqual(self.session_words().items(), dict(expected_result))
        self.assertListEqual(self.words.get_words(), expected_result)

    def test_clear_list(self):
        self.assertEqual(len(self.session_words()), 0)

        self.words.add_word('break', 'przerwa')
        self.words.add_word('code', 'kodować')
        self.words.add_word('attention', 'uwaga')

        self.assertEqual(len(self.session_words()), 3)

        self.words.clear_list()

        self.assertEqual(len(self.session_words()), 0)

    def test_save_to_db(self):
        self.assertEqual(len(self.dictionary.words), 0)

        self.words.add_word('break', 'przerwa')
        self.words.add_word('attention', 'uwaga')

        self.words.save_to_db()

        self.assertEqual(len(self.dictionary.words), 2)

        # testing if dictionary has been deleted from session
        self.assertNotIn(f"dictionary_{self.dictionary.id}", self.request.session)   

    def test_refresh_list(self):
        """
        `Words.refresh_list` undoes changes through copying words from `Dictionary` object.
        """
        self.assertEqual(len(self.session_words()), 0)
        self.assertEqual(len(self.dictionary.words), 0)

        self.words.add_word('break', 'przerwa')
        self.words.add_word('attention', 'uwaga')

        self.assertEqual(len(self.session_words()), 2)
        self.assertEqual(len(self.dictionary.words), 0)

        self.words.save_to_db()
        words = Words(self.request, self.dictionary)

        self.assertEqual(len(self.session_words()), 2)
        self.assertEqual(len(self.dictionary.words), 2)

        # Here the magic starts :)
        words.clear_list()

        self.assertEqual(len(self.session_words()), 0)
        self.assertEqual(len(self.dictionary.words), 2)

        words.refresh_list()

        self.assertEqual(len(self.session_words()), 2)
        self.assertEqual(len(self.dictionary.words), 2)


class TemplateFilterSimpleTestCase(SimpleTestCase):
    """
    Test of template filter `dictionary.templatetags.modi_extras.get_value`.
    """
    def setUp(self):
        self.sample_dictionary = {
            "first_key": "first_value",
            "second_key": "second_value",
        }
    
    def test_get_value_from_dict(self):
        self.assertEqual(get_value(self.sample_dictionary, 'first_key'),
                         "first_value")
        self.assertEqual(get_value(self.sample_dictionary, 'second_key'),
                         "second_value")
