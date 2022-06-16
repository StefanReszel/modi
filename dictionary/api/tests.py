from unittest.mock import Mock, patch

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from dictionary.models import Subject, Dictionary
from accounts.models import User
from dictionary.api.serializers import CustomUpdate
from dictionary.api.views import SearchMixin

from .permissions import IsOwnerPermission


class IsOwnerPermissionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

        cls.subject = Subject.objects.create(title="English",
                                             owner=cls.user)

        cls.dictionary = Dictionary.objects.create(title="Basic words",
                                                   subject=cls.subject,
                                                   words={'wojna': 'war'})

        cls.request = Mock()
        cls.request.user = cls.user

        cls.view = Mock()

    def setUp(self):
        self.per = IsOwnerPermission()

    def test_has_object_permission_should_return_true_when_object_is_a_dictionary(self):
        result = self.per.has_object_permission(self.request, self.view, self.dictionary)

        self.assertTrue(result)

    def test_has_object_permission_should_return_true_when_object_is_a_subject(self):
        result = self.per.has_object_permission(self.request, self.view, self.subject)

        self.assertTrue(result)


class CustomUpdateTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

        cls.subject = Subject.objects.create(title="English",
                                             owner=cls.user)

        cls.dictionary = Dictionary.objects.create(title="Basic words",
                                                   subject=cls.subject,
                                                   words={'wojna': 'war'})

    def setUp(self):
        self.validated_data = {
            'title': 'Polish',
            'words': {
                'love': 'miłość'
            }
        }

        self.cust_up_obj = CustomUpdate()

    def test_update_should_return_passed_subject_with_values_retrieved_form_validated_data(self):
        result = self.cust_up_obj.update(self.subject, self.validated_data)

        self.assertTrue(isinstance(result, Subject))
        self.assertEqual(result.title, self.validated_data['title'])
        self.assertFalse(hasattr(self.subject, 'words'))

    def test_update_should_return_passed_dictionary_with_values_retrieved_form_validated_data(self):
        result = self.cust_up_obj.update(self.dictionary, self.validated_data)

        self.assertTrue(isinstance(result, Dictionary))
        self.assertEqual(result.title, self.validated_data['title'])
        self.assertEqual(result.words, self.validated_data['words'])


class SearchMixinTestCase(APITestCase):
    def setUp(self):
        self.search_obj = SearchMixin()
        self.search_obj.request = Mock()
        self.queryset = ['unit', 'test']

    def test_return_found_or_all_should_return_all_when_query_is_none(self):
        self.search_obj.request.query_params.get.return_value = None
        result = self.search_obj.return_found_or_all(self.queryset)

        self.assertEqual(self.queryset, result)

    def test_return_found_or_all_should_return_all_when_queryset_is_empty(self):
        self.queryset = []
        result = self.search_obj.return_found_or_all(self.queryset)

        self.assertEqual(self.queryset, result)

    def test_return_found_or_all_should_return_all_when_query_is_an_empty_string(self):
        self.search_obj.request.query_params.get.return_value = ''
        result = self.search_obj.return_found_or_all(self.queryset)

        self.assertEqual(self.queryset, result)

    def test_return_found_or_all_should_return_found_when_wanted_exists_in_queryset(self):
        query = 'test'

        queryset = Mock()
        queryset.filter = Mock(return_value=query)

        result = self.search_obj.return_found_or_all(queryset)

        self.assertIn(result, self.queryset)

    def test_return_found_or_all_should_return_all_when_wanted_not_exists_in_queryset(self):
        queryset = Mock()
        queryset.__iter__ = Mock(return_value=iter(self.queryset))
        queryset.filter = Mock(return_value=[])

        result = list(self.search_obj.return_found_or_all(queryset))

        self.assertEqual(self.queryset, result)


class SubjectViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

        cls.subject = Subject.objects.create(title="English",
                                             owner=cls.user)

    def setUp(self):
        self.client.login(username='TestUser', password='test1234')

    def test_http_get_method_should_return_status_200_when_list_of_subjects_requested(self):
        response = self.client.get(reverse('subject-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_http_post_method_should_return_status_200_when_list_of_subjects_requested(self):
        response = self.client.get(reverse('subject-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_http_post_method_should_return_status_201_when_requested_with_valid_data(self):
        response = self.client.post(reverse('subject-list'),
                                    data={'title': 'Polish'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_http_post_method_should_increase_amount_of_subjects_when_requested_with_valid_data(self):
        dictionaries_before = Subject.objects.count()

        self.client.post(reverse('subject-list'),
                         data={'title': 'Polish'})

        dictionaries_after = Subject.objects.count()

        self.assertGreater(dictionaries_after, dictionaries_before)

    def test_http_post_method_should_return_status_400_when_requested_with_data_of_existed_subject(self):
        response = self.client.post(reverse('subject-list'),
                                    data={'title': 'English'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DictionaryViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

        cls.subject = Subject.objects.create(title="English",
                                             owner=cls.user)

        cls.dictionary = Dictionary.objects.create(title="Basic words",
                                                   subject=cls.subject,
                                                   words={'wojna': 'war'})

    def setUp(self):
        self.client.login(username='TestUser', password='test1234')

    def test_http_get_method_should_return_status_200_when_list_of_dictionaries_requested_with_valid_args(self):
        response = self.client.get(reverse('dictionary-list', args=[self.subject.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_http_get_method_should_return_status_404_when_requested_with_invalid_args(self):
        response = self.client.get(reverse('dictionary-list', args=[self.subject.id + 1]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_http_post_method_should_return_status_201_when_requested_with_valid_data(self):
        response = self.client.post(reverse('dictionary-list', args=[self.subject.id]),
                                    data={'title': 'Popular words'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_http_post_method_should_increase_amount_of_dictionaries_when_requested_with_valid_data(self):
        dictionaries_before = Dictionary.objects.count()

        self.client.post(reverse('dictionary-list', args=[self.subject.id]),
                         data={'title': 'Popular words'})

        dictionaries_after = Dictionary.objects.count()

        self.assertGreater(dictionaries_after, dictionaries_before)

    def test_http_post_method_should_return_status_400_when_requested_with_data_of_existed_dictionary(self):
        response = self.client.post(reverse('dictionary-list', args=[self.subject.id]),
                                    data={'title': 'Basic words'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class WordsRequestsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

        cls.subject = Subject.objects.create(title="English",
                                             owner=cls.user)

        cls.dictionary = Dictionary.objects.create(title="Basic words",
                                                   subject=cls.subject,
                                                   words={'wojna': 'war'})

    def setUp(self):
        self.client.login(username='TestUser', password='test1234')

    def test_http_get_method_should_return_status_200_when_list_of_words_from_dictionary_requested_with_valid_args(self):
        response = self.client.get(reverse('dictionary-words', args=[self.subject.id, self.dictionary.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_http_get_method_should_return_status_200_when_list_of_words_from_session_requested_with_valid_args(self):
        response = self.client.get(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_http_post_method_should_return_status_200(self):
        response = self.client.post(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]),
                                    data={"word": "cat", "definition": "kot"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('dictionary.words.Words.save_to_db')
    def test_http_post_method_should_invoke_save_to_db_method_of_words_class(self, save_to_db_mock):
        self.client.post(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]),
                         data={"word": "cat", "definition": "kot"})

        save_to_db_mock.assert_called()

    def test_http_put_method_should_return_status_200(self):
        response = self.client.put(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]),
                                   data={"word": "cat", "definition": "kot"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_http_put_method_should_return_status_400_when_definition_in_provided_data_already_exists_in_words(self):
        response = self.client.put(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]),
                                   data={"word": "war", "definition": "wojna"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('dictionary.words.Words.add_word')
    def test_http_put_method_should_invoke_add_word_method_of_words_class(self, add_word_mock):
        self.client.put(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]),
                        data={"word": "cat", "definition": "kot"})

        add_word_mock.assert_called()

    def test_http_delete_method_should_return_status_200(self):
        response = self.client.delete(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]),
                                      data={"definition": "wojna"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('dictionary.words.Words.remove_word')
    def test_http_delete_method_should_invoke_remove_word_method_of_words_class(self, remove_word_mock):
        self.client.delete(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]),
                           data={"definition": "wojna"})

        remove_word_mock.assert_called()

    def test_http_delete_method_should_return_status_400_when_provided_definition_does_not_exist_in_words(self):
        response = self.client.delete(reverse('dictionary-edit-words', args=[self.subject.id, self.dictionary.id]),
                                      data={"definition": "nonexisted"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('dictionary.words.Words.refresh_list')
    def test_http_post_method_should_invoke_refresh_list_method_of_words_class(self, refresh_list_mock):
        self.client.post(reverse('dictionary-refresh-words', args=[self.subject.id, self.dictionary.id]))

        refresh_list_mock.assert_called()
