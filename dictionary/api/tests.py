"""
Tested modules:
    - `dictionary.api.permissions`
    - `dictionary.api.serializers`
    - `dictionary.api.views`
"""
from django.urls import reverse
from django.db import transaction
from rest_framework import status
from rest_framework.test import APITestCase

from dictionary.models import Subject, Dictionary
from accounts.models import User
from dictionary.api.serializers import SubjectSerializer, DictionarySerializer


class PermissionsAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')
        cls.user_subject = Subject.objects.create(title="Język angielski", owner=cls.user)
        cls.user_dictionary = Dictionary.objects.create(title="słówka z podręcznika", subject=cls.user_subject)

        cls.another_user = User.objects.create_user(email='another-test@email.com',
                                                    username='AnotherTestUser',
                                                    password='test1234')
        cls.another_user_subject = Subject.objects.create(title="Język łaciński", owner=cls.another_user)
        cls.another_user_dictionary = Dictionary.objects.create(title="różne słówka", subject=cls.another_user_subject)

    def test_is_owner_permission(self):
        # one user
        self.client.login(username='TestUser', password='test1234')

        # Subject
        response = self.client.get(reverse('subject-detail', args=[self.user_subject.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('subject-detail', args=[self.another_user_subject.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Dictionary
        response = self.client.get(reverse('dictionary-detail', args=[self.user_subject.id, self.user_dictionary.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('dictionary-detail',
                                   args=[self.another_user_subject.id, self.another_user_dictionary.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # another user
        self.client.login(username='AnotherTestUser', password='test1234')

        # Subject
        response = self.client.get(reverse('subject-detail', args=[self.another_user_subject.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('subject-detail', args=[self.user_subject.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Dictionary
        response = self.client.get(reverse('dictionary-detail',
                                   args=[self.another_user_subject.id, self.another_user_dictionary.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('dictionary-detail', args=[self.user_subject.id, self.user_dictionary.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SerializersAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')
        cls.subject = Subject.objects.create(title="Język angielski", owner=cls.user)
        cls.dictionary = Dictionary.objects.create(title="słówka z podręcznika",
                                                   subject=cls.subject,
                                                   description="Słówka z podrecznika szkolnego")

    def test_custom_update(self):
        """
        Test of `dictionary.api.serializers.CustomUpdate`
        """
        # Subject
        new_title = "Język niemiecki"
        serializer = SubjectSerializer(self.subject, data={'title': new_title}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(self.subject.title, new_title)

        # Dictionary
        new_title = "słówka z książki"

        serializer = DictionarySerializer(self.dictionary, data={'title': new_title}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(self.dictionary.title, new_title)

        new_description = "słówka z nowej książki"
        serializer = DictionarySerializer(self.dictionary, data={'description': new_description}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(self.dictionary.description, new_description)


class ViewsAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='test@email.com',
                                            username='TestUser',
                                            password='test1234')

        Subject.objects.create(title="Język angielski", owner=cls.user)
        Subject.objects.create(title="Język niemiecki", owner=cls.user)
        Subject.objects.create(title="Język hiszpański", owner=cls.user)

        Dictionary.objects.create(title="słówka z podręcznika", subject=Subject.objects.get(id=1),
                                  words={"krowa": "cow", "pies": "dog"})
        Dictionary.objects.create(title="słówka z filmu Star Wars", subject=Subject.objects.get(id=1))
        Dictionary.objects.create(title="słówka z książki Wiedźmin", subject=Subject.objects.get(id=1))

        Dictionary.objects.create(title="różne słówka", subject=Subject.objects.get(id=2))
        Dictionary.objects.create(title="inne słówka", subject=Subject.objects.get(id=2))

    def setUp(self):
        self.client.login(username='TestUser', password='test1234')

    def test_response_status(self):
        # existed `Subject`
        response = self.client.get(reverse('subject-detail', args=[1]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # nonexisted `Subject`
        response = self.client.get(reverse('subject-detail', args=[10]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # existed `Subject`
        response = self.client.get(reverse('dictionary-list', args=[1]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # nonexisted `Subject`
        response = self.client.get(reverse('dictionary-list', args=[10]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # existed `Subject` and `Dictionary`
        response = self.client.get(reverse('dictionary-detail',
                                   args=[1, 1]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # nonexisted `Subject` and existed `Dictionary`
        response = self.client.get(reverse('dictionary-detail',
                                   args=[10, 1]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # existed `Subject` and nonexisted `Dictionary`
        response = self.client.get(reverse('dictionary-detail',
                                   args=[1, 10]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # nonexisted `Subject` and nonexisted `Dictionary`
        response = self.client.get(reverse('dictionary-detail',
                                   args=[10, 10]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_mixin(self):
        """
        Test of `dictionary.api.views.SearchMixin.return_found_or_all`.
        """
        # Test of `Subject`
        # a case with no data
        response = self.client.get(reverse('subject-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # a case with data
        response = self.client.get(reverse('subject-list'), data={'search': 'yk nie'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(reverse('subject-list'), data={'search': 'jezyk'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(reverse('subject-list'), data={'search': 'angielski'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # a case with nonexistent object or which not belongs to logged user
        response = self.client.get(reverse('subject-list'), data={'search': 'łaciński'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(reverse('subject-list'), data={'search': 'kaszubski'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # Test of `Dictionary`
        # a case with no data
        response = self.client.get(reverse('dictionary-list', args=[1]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # a case with data
        response = self.client.get(reverse('dictionary-list', args=[1]), data={'search': 'star wa'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(reverse('dictionary-list', args=[1]), data={'search': 'slowka'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # a case with nonexistent object or which is not related with chosen `Subject` object
        response = self.client.get(reverse('dictionary-list', args=[1]), data={'search': 'książka'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(reverse('dictionary-list', args=[1]), data={'search': 'różne'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_perform_create(self):
        # Test of `Subject`
        self.assertEqual(len(self.user.subjects.all()), 3)

        response = self.client.post(reverse('subject-list'), data={'title': 'Język japoński'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.user.subjects.all()), 4)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # a case when the same object already exists
        with transaction.atomic():
            response = self.client.post(reverse('subject-list'), data={'title': 'Język angielski'})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test of `Dictionary`
        self.assertEqual(len(self.user.subjects.get(id=1).dicts.all()), 3)

        response = self.client.post(reverse('dictionary-list', args=[1]),
                                    data={'title': 'słówka z życia codziennego',
                                          'description': 'Słówka, które przetłumaczyłem na własne potrzeby.'})
        self.assertEqual(len(self.user.subjects.get(id=1).dicts.all()), 4)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # a case when the same object already exists
        with transaction.atomic():
            response = self.client.post(reverse('dictionary-list', args=[1]), data={'title': 'słówka z podręcznika'})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_words(self):
        response = self.client.get(reverse('dictionary-words', args=[1, 1]))
        dictionary = Dictionary.objects.get(id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, dictionary.words)

    def test_edit_words(self):
        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        dictionary = Dictionary.objects.get(id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data, dictionary.words)

    def test_add_word(self):
        response = self.client.put(reverse('dictionary-edit-words', args=[1, 1]),
                                   data={"word": "cat", "definition": "kot"})
        dictionary = Dictionary.objects.get(id=1)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 3)
        self.assertNotEqual(dictionary.words, response.data)

        # a case with no provided data
        response = self.client.put(reverse('dictionary-edit-words', args=[1, 1]),
                                   data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # a case when the same definition is in session
        response = self.client.put(reverse('dictionary-edit-words', args=[1, 1]),
                                   data={"word": "dog", "definition": "pies"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        self.assertEqual(len(response.data), 3)

    def test_delete_word(self):
        response = self.client.delete(reverse('dictionary-edit-words', args=[1, 1]),
                                      data={"definition": "pies"})
        dictionary = Dictionary.objects.get(id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertNotEqual(dictionary.words, response.data)

        # a case with no provided, or wrong data
        response = self.client.delete(reverse('dictionary-edit-words', args=[1, 1]),
                                      data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        self.assertEqual(len(response.data), 1)

        response = self.client.delete(reverse('dictionary-edit-words', args=[1, 1]),
                                      data={"definition": "wakacje"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        self.assertEqual(len(response.data), 1)

    def test_refresh_words(self):
        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        self.assertEqual(len(response.data), 2)

        self.client.delete(reverse('dictionary-edit-words', args=[1, 1]),
                           data={"definition": "pies"})
        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        self.assertEqual(len(response.data), 1)

        response = self.client.post(reverse('dictionary-refresh-words', args=[1, 1]))
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        self.assertEqual(len(response.data), 2)

        self.client.put(reverse('dictionary-edit-words', args=[1, 1]),
                        data={"word": "cat", "definition": "kot"})
        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        self.assertEqual(len(response.data), 3)

        response = self.client.post(reverse('dictionary-refresh-words', args=[1, 1]))
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse('dictionary-edit-words', args=[1, 1]))
        self.assertEqual(len(response.data), 2)

    def test_save_words(self):
        dictionary = Dictionary.objects.get(id=1)
        self.assertEqual(len(dictionary.words), 2)

        self.client.put(reverse('dictionary-edit-words', args=[1, 1]),
                        data={"word": "cat", "definition": "kot"})

        dictionary = Dictionary.objects.get(id=1)
        self.assertEqual(len(dictionary.words), 2)

        self.client.post(reverse('dictionary-edit-words', args=[1, 1]))

        dictionary = Dictionary.objects.get(id=1)
        self.assertEqual(len(dictionary.words), 3)

        self.client.delete(reverse('dictionary-edit-words', args=[1, 1]),
                           data={"definition": "kot"})

        self.client.delete(reverse('dictionary-edit-words', args=[1, 1]),
                           data={"definition": "pies"})

        dictionary = Dictionary.objects.get(id=1)
        self.assertEqual(len(dictionary.words), 3)

        self.client.post(reverse('dictionary-edit-words', args=[1, 1]))

        dictionary = Dictionary.objects.get(id=1)
        self.assertEqual(len(dictionary.words), 1)
