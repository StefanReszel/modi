from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode

from accounts.models import User
from dictionary.models import Subject, Dictionary


class SubjectViewsTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@email.com',
                                             username='TestUser',
                                             password='test1234')
        self.client.login(username='TestUser', password='test1234')

    def test_get_list(self):
        """
        Test of `dictionary.views.SearchMixin.return_found_or_all`
        """
        # when user has empty queryset of subjects
        response = self.client.get(reverse('dictionary:subject_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['subject_list'].count(), 0)
        self.assertTemplateUsed(response, 'modi/search_form.html')

        # adding a few `Subject` objects and different `User` with `Subject` object
        different_user = User.objects.create_user(email='random@email.com',
                                                  username='RandomUser',
                                                  password='test1234')

        Subject.objects.create(title='Język angielski', owner=self.user)
        Subject.objects.create(title='Język łaciński', owner=self.user)
        Subject.objects.create(title='Język hiszpański', owner=different_user)

        logged_user_subjects = self.user.subjects.all()

        # when no query
        response = self.client.get(reverse('dictionary:subject_list'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['subject_list'], logged_user_subjects)

        # when query is empty
        response = self.client.get(reverse('dictionary:subject_list'), data={'search': ''})
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['subject_list'], logged_user_subjects)

        # when there is query
        response = self.client.get(reverse('dictionary:subject_list'), data={'search': 'zyk'})
        expected_result = logged_user_subjects.filter(slug__icontains='zyk')
        self.assertQuerysetEqual(response.context['subject_list'], expected_result)

        response = self.client.get(reverse('dictionary:subject_list'), data={'search': 'jezyk angielski'})
        expected_result = logged_user_subjects.filter(slug__icontains='jezyk-angielski')
        self.assertQuerysetEqual(response.context['subject_list'], expected_result)

        response = self.client.get(reverse('dictionary:subject_list'), data={'search': 'łaciń'})
        expected_result = logged_user_subjects.filter(slug__icontains='lacin')
        self.assertQuerysetEqual(response.context['subject_list'], expected_result)

        # when object does not exist or belongs to another user
        response = self.client.get(reverse('dictionary:subject_list'), data={'search': 'hiszpański'})
        self.assertQuerysetEqual(response.context['subject_list'], logged_user_subjects)

        response = self.client.get(reverse('dictionary:subject_list'), data={'search': 'japonski'})
        self.assertQuerysetEqual(response.context['subject_list'], logged_user_subjects)

    def test_create(self):
        # test GET
        response = self.client.get(reverse('dictionary:subject_create'))
        self.assertEqual(response.status_code, 200)

        # create by POST
        response = self.client.post(reverse('dictionary:subject_create'), data={"title": "Język angielski"})

        self.assertEqual(Subject.objects.count(), 1)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, Subject.objects.last().get_absolute_url())

        # a case with the same, or similar title
        response = self.client.post(reverse('dictionary:subject_create'), data={"title": "Język angielski"})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('dictionary:subject_create'), data={"title": "jezyk angielski"})
        self.assertEqual(response.status_code, 200)

        # a case with no data
        response = self.client.post(reverse('dictionary:subject_create'), data={"title": ""})
        self.assertEqual(response.status_code, 200)

    def test_update(self):
        # creating `Subject` object to updates
        subject = Subject.objects.create(title='Język angielski', owner=self.user)

        # test GET
        response = self.client.get(reverse('dictionary:subject_update', args=[subject.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('subject', response.context)

        # update by POST
        new_title = 'Język Niemiecki'
        response = self.client.post(reverse('dictionary:subject_update', args=[subject.slug]),
                                    data={'title': new_title})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:dict_list', args=[slugify(unidecode(new_title))]))

        # update using already existing title
        subject = Subject.objects.create(title='Język Hiszpański', owner=self.user)  # another Subject

        new_title = 'Język Niemiecki'
        response = self.client.post(reverse('dictionary:subject_update', args=[subject.slug]),
                                    data={'title': new_title})
        self.assertEqual(response.status_code, 200)

        new_title = 'jezyk niemiecki'
        response = self.client.post(reverse('dictionary:subject_update', args=[subject.slug]),
                                    data={'title': new_title})
        self.assertEqual(response.status_code, 200)

        # checking whether object in context has a primal title
        self.assertEqual(response.context['subject'].title, 'Język Hiszpański')

        # a case with no data
        response = self.client.post(reverse('dictionary:subject_update', args=[subject.slug]), data={"title": ""})
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        self.assertEqual(self.user.subjects.count(), 0)

        # creating `Subject` object to delete
        subject = Subject.objects.create(title='Język angielski', owner=self.user)
        self.assertEqual(self.user.subjects.count(), 1)

        # test GET
        response = self.client.get(reverse('dictionary:subject_delete', args=[subject.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'modi/delete_form.html')
        self.assertIn('subject', response.context)

        # delete by POST
        response = self.client.post(reverse('dictionary:subject_delete', args=[subject.id]))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:subject_list'))
        self.assertEqual(self.user.subjects.count(), 0)


class DictionaryViewsTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@email.com',
                                             username='TestUser',
                                             password='test1234')
        self.subject = Subject.objects.create(title='Język angielski', owner=self.user)

        self.client.login(username='TestUser', password='test1234')

    def test_get_list(self):
        """
        Test of `dictionary.views.SearchMixin.return_found_or_all`
        """
        # when subject has not any dictionaries
        response = self.client.get(reverse('dictionary:dict_list', args=[self.subject.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('subject', response.context)
        self.assertEqual(response.context['dictionary_list'].count(), 0)
        self.assertTemplateUsed(response, 'modi/search_form.html')

        # adding a few `Dictonary` objects and different `Subject` with `Dictionary` object
        different_subject = Subject.objects.create(title='Język hiszpański', owner=self.user)

        Dictionary.objects.create(title='Książka "Lord of the Rings"', subject=self.subject)
        Dictionary.objects.create(title='Film "Titanic"', subject=self.subject)
        Dictionary.objects.create(title='Książka "Harry Potter"', subject=different_subject)

        concrete_dictionaries = Dictionary.objects.filter(subject=self.subject)

        # when no query
        response = self.client.get(reverse('dictionary:dict_list', args=[self.subject.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['dictionary_list'], concrete_dictionaries)

        # when query is empty
        response = self.client.get(reverse('dictionary:dict_list', args=[self.subject.slug]),
                                   data={'search': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIn('subject', response.context)
        self.assertQuerysetEqual(response.context['dictionary_list'], concrete_dictionaries)

        # when there is query
        response = self.client.get(reverse('dictionary:dict_list', args=[self.subject.slug]),
                                   data={'search': 'titanic'})
        expected_result = concrete_dictionaries.filter(slug__icontains='titanic')
        self.assertQuerysetEqual(response.context['dictionary_list'], expected_result)

        response = self.client.get(reverse('dictionary:dict_list', args=[self.subject.slug]),
                                   data={'search': 'książka lord of '})
        expected_result = concrete_dictionaries.filter(slug__icontains='ksiazka-lord-of')
        self.assertQuerysetEqual(response.context['dictionary_list'], expected_result)

        response = self.client.get(reverse('dictionary:dict_list', args=[self.subject.slug]),
                                   data={'search': 'Film "Titanic"'})
        expected_result = concrete_dictionaries.filter(slug__icontains='film-titanic')
        self.assertQuerysetEqual(response.context['dictionary_list'], expected_result)

        # when object does not exist or is in another subject
        response = self.client.get(reverse('dictionary:dict_list', args=[self.subject.slug]),
                                   data={'search': 'harry potter'})
        self.assertQuerysetEqual(response.context['dictionary_list'], concrete_dictionaries)

        response = self.client.get(reverse('dictionary:dict_list', args=[self.subject.slug]),
                                   data={'search': 'Podręcznik'})
        self.assertQuerysetEqual(response.context['dictionary_list'], concrete_dictionaries)

    def test_create(self):
        # test GET
        response = self.client.get(reverse('dictionary:dict_create', args=[self.subject.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('subject', response.context)

        # create by POST
        response = self.client.post(reverse('dictionary:dict_create', args=[self.subject.slug]),
                                    data={"title": "Władca pierścieni",
                                          "description": "Słowka z filmu."})

        self.assertEqual(self.subject.dicts.count(), 1)
        dictionary = Dictionary.objects.last()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:word_form', args=[dictionary.subject.slug, dictionary.slug]))

        # a case with the same, or similar title
        response = self.client.post(reverse('dictionary:dict_create', args=[self.subject.slug]),
                                    data={"title": "wladca pierscieni"})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('dictionary:dict_create', args=[self.subject.slug]),
                                    data={"title": "Władca pierścieni"})
        self.assertEqual(response.status_code, 200)

        # a case with no data
        response = self.client.post(reverse('dictionary:dict_create', args=[self.subject.slug]),
                                    data={"title": ""})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('dictionary:dict_create', args=[self.subject.slug]),
                                    data={'title': '', 'description': 'Opis'})
        self.assertEqual(response.status_code, 200)

    def test_update(self):
        # creating `Dictionary` object to updates
        dictionary = Dictionary.objects.create(title='Podręcznik', description='Klasa I', subject=self.subject)

        # test GET
        response = self.client.get(reverse('dictionary:dict_update', args=[dictionary.subject.slug, dictionary.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('dictionary', response.context)

        # update by POST
        new_title = 'Książka'
        response = self.client.post(reverse('dictionary:dict_update', args=[dictionary.subject.slug, dictionary.slug]),
                                    data={'title': new_title})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:dict_detail',
                                               args=[dictionary.subject.slug, slugify(unidecode(new_title))]))

        # update using already existing title
        dictionary = Dictionary.objects.create(title='Lektura', subject=self.subject)  # another Dictionary

        new_title = 'Książka'
        response = self.client.post(reverse('dictionary:dict_update', args=[dictionary.subject.slug, dictionary.slug]),
                                    data={'title': new_title})
        self.assertEqual(response.status_code, 200)

        new_title = 'ksiazka'
        response = self.client.post(reverse('dictionary:dict_update', args=[dictionary.subject.slug, dictionary.slug]),
                                    data={'title': new_title})
        self.assertEqual(response.status_code, 200)

        # checking whether object in context has a primal title
        self.assertEqual(response.context['dictionary'].title, 'Lektura')

        # a case with no data
        response = self.client.post(reverse('dictionary:dict_update', args=[dictionary.subject.slug, dictionary.slug]),
                                    data={"title": ""})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('dictionary:dict_update', args=[dictionary.subject.slug, dictionary.slug]),
                                    data={'title': '', 'description': 'Opis'})
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        self.assertEqual(self.subject.dicts.count(), 0)

        # creating `Dictionary` object to delete
        dictionary = Dictionary.objects.create(title='Książka', subject=self.subject)
        self.assertEqual(self.subject.dicts.count(), 1)

        # test GET
        response = self.client.get(reverse('dictionary:dict_delete', args=[dictionary.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('dictionary', response.context)
        self.assertTemplateUsed(response, 'modi/delete_form.html')

        # delete by POST
        response = self.client.post(reverse('dictionary:dict_delete', args=[dictionary.id]))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:dict_list', args=[dictionary.subject.slug]))
        self.assertEqual(self.subject.dicts.count(), 0)


class WordFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')
        cls.subject = Subject.objects.create(title='Język angielski',
                                             owner=cls.user)
        cls.dictionary = Dictionary.objects.create(title='Podręcznik',
                                                   description='Klasa I',
                                                   subject=cls.subject)

    def setUp(self):
        self.client.login(username='TestUser', password='test1234')

    def test_word_form(self):
        # test GET
        response = self.client.get(reverse('dictionary:word_form',
                                           args=[self.dictionary.subject.slug, self.dictionary.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('dictionary', response.context)

        # test POST
        response = self.client.post(reverse('dictionary:word_form',
                                            args=[self.dictionary.subject.slug, self.dictionary.slug]),
                                    data={'word': 'thus', 'definition': 'stąd'})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:word_form',
                                               args=[self.dictionary.subject.slug, self.dictionary.slug]))

        # when the definition already exists
        response = self.client.post(reverse('dictionary:word_form',
                                            args=[self.dictionary.subject.slug, self.dictionary.slug]),
                                    data={'word': 'hence', 'definition': 'stąd'})

        self.assertEqual(response.status_code, 200)

        # with no data
        response = self.client.post(reverse('dictionary:word_form',
                                            args=[self.dictionary.subject.slug, self.dictionary.slug]),
                                    data={'word': '', 'definition': ''})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('dictionary:word_form',
                                            args=[self.dictionary.subject.slug, self.dictionary.slug]),
                                    data={'word': '', 'definition': 'stąd'})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('dictionary:word_form',
                                            args=[self.dictionary.subject.slug, self.dictionary.slug]),
                                    data={'word': 'hence', 'definition': ''})
        self.assertEqual(response.status_code, 200)


class WordsManagementView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')
        cls.subject = Subject.objects.create(title='Język angielski',
                                             owner=cls.user)
        cls.dictionary = Dictionary.objects.create(title='Podręcznik',
                                                   description='Klasa I',
                                                   subject=cls.subject,
                                                   words={'gitara': 'guitar'})

    def setUp(self):
        self.client.login(username='TestUser', password='test1234')

    def test_actions(self):
        response = self.client.post(reverse('dictionary:word_delete', args=[self.dictionary.id]),
                                    data={'definition': 'gitara'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:word_form',
                                               args=[self.dictionary.subject.slug, self.dictionary.slug]))

        response = self.client.post(reverse('dictionary:refresh_list', args=[self.dictionary.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:word_form',
                                               args=[self.dictionary.subject.slug, self.dictionary.slug]))

        response = self.client.post(reverse('dictionary:clear_list', args=[self.dictionary.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:word_form',
                                               args=[self.dictionary.subject.slug, self.dictionary.slug]))

        response = self.client.post(reverse('dictionary:confirm_changes', args=[self.dictionary.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dictionary:dict_detail',
                                               args=[self.dictionary.subject.slug, self.dictionary.slug]))


class LearningViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')
        cls.subject = Subject.objects.create(title='Język angielski',
                                             owner=cls.user)
        cls.dictionary = Dictionary.objects.create(title='Podręcznik',
                                                   subject=cls.subject)

    def setUp(self):
        self.client.login(username='TestUser', password='test1234')

    def test_learning(self):
        response = self.client.get(reverse('dictionary:learning',
                                           args=[self.dictionary.subject.slug, self.dictionary.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('dictionary', response.context)

    def test_complete(self):
        response = self.client.get(reverse('dictionary:complete',
                                           args=[self.dictionary.subject.slug, self.dictionary.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('dictionary', response.context)
