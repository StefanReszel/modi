from unittest.mock import Mock

from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from accounts.models import User
from dictionary.models import Subject, Dictionary
from dictionary.views import SearchMixin


class SearchMixinTestCase(TestCase):
    def setUp(self):
        self.search_obj = SearchMixin()
        self.search_obj.request = Mock()
        self.queryset = ["unit", "test"]

    def test_return_found_or_all_should_return_all_when_query_is_none(self):
        self.search_obj.request.GET.get.return_value = None
        result = self.search_obj.return_found_or_all(self.queryset)

        self.assertEqual(self.queryset, result)

    def test_return_found_or_all_should_return_all_when_queryset_is_empty(self):
        self.queryset = []
        result = self.search_obj.return_found_or_all(self.queryset)

        self.assertEqual(self.queryset, result)

    def test_return_found_or_all_should_return_all_when_query_is_an_empty_string(self):
        self.search_obj.request.GET.get.return_value = ""
        result = self.search_obj.return_found_or_all(self.queryset)

        self.assertEqual(self.queryset, result)

    def test_return_found_or_all_should_return_found_when_wanted_exists_in_queryset(
        self,
    ):
        query = "test"

        queryset = Mock()
        queryset.filter = Mock(return_value=query)

        result = self.search_obj.return_found_or_all(queryset)

        self.assertIn(result, self.queryset)

    def test_return_found_or_all_should_return_all_when_wanted_not_exists_in_queryset(
        self,
    ):
        queryset = Mock()
        queryset.__iter__ = Mock(return_value=iter(self.queryset))
        queryset.filter = Mock(return_value=[])

        result = list(self.search_obj.return_found_or_all(queryset))

        self.assertEqual(self.queryset, result)


class SubjectListViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

    def setUp(self):
        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(reverse("dictionary:subject_list"))

        self.assertEqual(response.status_code, 200)


class SubjectCreateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        cls.subject = Subject.objects.create(title="English", owner=cls.user)

    def setUp(self):
        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(reverse("dictionary:subject_create"))

        self.assertEqual(response.status_code, 200)

    def test_http_post_method_response_should_return_status_302_when_valid_data_provided(
        self,
    ):
        response = self.client.post(
            reverse("dictionary:subject_create"), data={"title": "Polish"}
        )

        self.assertEqual(response.status_code, 302)

    def test_http_post_method_response_should_increase_amount_of_subjects(self):
        subjects_before = Subject.objects.count()

        self.client.post(reverse("dictionary:subject_create"), data={"title": "Polish"})

        subjects_after = Subject.objects.count()

        self.assertGreater(subjects_after, subjects_before)

    def test_http_post_method_response_should_return_status_200_when_attempt_to_create_existed_subject(
        self,
    ):
        response = self.client.post(
            reverse("dictionary:subject_create"), data={"title": self.subject.title}
        )

        self.assertEqual(response.status_code, 200)


class SubjectUpdateViewTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        self.subject = Subject.objects.create(title="English", owner=self.user)

        self.another_subject = Subject.objects.create(title="Polish", owner=self.user)

        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(
            reverse("dictionary:subject_update", args=[self.subject.slug])
        )

        self.assertEqual(response.status_code, 200)

    def test_http_post_method_response_should_return_status_302_when_valid_data_provided(
        self,
    ):
        new_title = "Spain"

        response = self.client.post(
            reverse("dictionary:subject_update", args=[self.subject.slug]),
            data={"title": new_title},
        )

        self.assertEqual(response.status_code, 302)

    def test_http_post_method_response_should_return_status_200_when_attempt_to_update_data_to_data_of_existed_subject(
        self,
    ):
        response = self.client.post(
            reverse("dictionary:subject_update", args=[self.subject.slug]),
            data={"title": self.another_subject.title},
        )

        self.assertEqual(response.status_code, 200)

    def test_http_post_method_when_attempt_to_update_data_to_data_of_existed_subject_response_should_contains_original_title(
        self,
    ):
        response = self.client.post(
            reverse("dictionary:subject_update", args=[self.subject.slug]),
            data={"title": self.another_subject.title},
        )

        self.assertContains(response, self.subject.title)


class SubjectDeleteViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        cls.subject = Subject.objects.create(title="English", owner=cls.user)

    def setUp(self):
        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(
            reverse("dictionary:subject_delete", args=[self.subject.id])
        )

        self.assertEqual(response.status_code, 200)

    def test_http_get_method_response_should_use_concrete_template(self):
        response = self.client.get(
            reverse("dictionary:subject_delete", args=[self.subject.id])
        )

        self.assertTemplateUsed(response, "modi/delete_form.html")

    def test_http_post_method_response_should_return_status_302(self):
        response = self.client.post(
            reverse("dictionary:subject_delete", args=[self.subject.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_http_post_method_response_should_decrease_amount_of_subjects(self):
        subjects_before = Subject.objects.count()

        self.client.post(reverse("dictionary:subject_delete", args=[self.subject.id]))

        subjects_after = Subject.objects.count()

        self.assertLess(subjects_after, subjects_before)


class DictionaryListViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        cls.subject = Subject.objects.create(title="English", owner=cls.user)

    def setUp(self):
        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(
            reverse("dictionary:dict_list", args=[self.subject.slug])
        )

        self.assertEqual(response.status_code, 200)


class DictionaryCreateViewTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        self.subject = Subject.objects.create(title="English", owner=self.user)

        self.dictionary = Dictionary.objects.create(
            title="Basic words", subject=self.subject
        )

        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(
            reverse("dictionary:dict_create", args=[self.subject.slug])
        )

        self.assertEqual(response.status_code, 200)

    def test_http_post_method_response_should_return_status_302_when_valid_data_provided(
        self,
    ):
        response = self.client.post(
            reverse("dictionary:dict_create", args=[self.subject.slug]),
            data={"title": "Popular words"},
        )

        self.assertEqual(response.status_code, 302)

    def test_http_post_method_response_should_increase_amount_of_dictionaries(self):
        dictionaries_before = Dictionary.objects.count()

        self.client.post(
            reverse("dictionary:dict_create", args=[self.subject.slug]),
            data={"title": "Popular words"},
        )

        dictionaries_after = Dictionary.objects.count()

        self.assertGreater(dictionaries_after, dictionaries_before)

    def test_http_post_method_response_should_return_status_200_when_attempt_to_create_existed_dictionary(
        self,
    ):
        response = self.client.post(
            reverse("dictionary:dict_create", args=[self.subject.slug]),
            data={"title": self.dictionary.title},
        )

        self.assertEqual(response.status_code, 200)


class DictionaryUpdateViewTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        self.subject = Subject.objects.create(title="English", owner=self.user)

        self.dictionary = Dictionary.objects.create(
            title="Basic words", subject=self.subject
        )

        self.another_dictionary = Dictionary.objects.create(
            title="Popular words", subject=self.subject
        )

        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(
            reverse(
                "dictionary:dict_update", args=[self.subject.slug, self.dictionary.slug]
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_http_post_method_response_should_return_status_302_when_valid_data_provided(
        self,
    ):
        new_title = "Important words"

        response = self.client.post(
            reverse(
                "dictionary:dict_update", args=[self.subject.slug, self.dictionary.slug]
            ),
            data={"title": new_title},
        )

        self.assertEqual(response.status_code, 302)

    def test_http_post_method_response_should_return_status_200_when_attempt_to_update_data_to_data_of_existed_dictionary(
        self,
    ):
        response = self.client.post(
            reverse(
                "dictionary:dict_update", args=[self.subject.slug, self.dictionary.slug]
            ),
            data={"title": self.another_dictionary.title},
        )

        self.assertEqual(response.status_code, 200)

    def test_http_post_method_when_attempt_to_update_data_to_data_of_existed_dictionary_response_should_contains_original_title(
        self,
    ):
        response = self.client.post(
            reverse(
                "dictionary:dict_update", args=[self.subject.slug, self.dictionary.slug]
            ),
            data={"title": self.another_dictionary.title},
        )

        self.assertContains(response, self.dictionary.title)


class DictionaryDeleteViewTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        self.subject = Subject.objects.create(title="English", owner=self.user)

        self.dictionary = Dictionary.objects.create(
            title="Basic words", subject=self.subject
        )

        self.another_dictionary = Dictionary.objects.create(
            title="Popular words", subject=self.subject
        )

        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(
            reverse("dictionary:dict_delete", args=[self.dictionary.id])
        )

        self.assertEqual(response.status_code, 200)

    def test_http_get_method_response_should_use_concrete_template(self):
        response = self.client.get(
            reverse("dictionary:dict_delete", args=[self.dictionary.id])
        )

        self.assertTemplateUsed(response, "modi/delete_form.html")

    def test_http_post_method_response_should_return_status_302(self):
        response = self.client.post(
            reverse("dictionary:dict_delete", args=[self.dictionary.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_http_post_method_response_should_increase_amount_of_dictionaries(self):
        dictionaries_before = Dictionary.objects.count()

        self.client.post(reverse("dictionary:dict_delete", args=[self.dictionary.id]))

        dictionaries_after = Dictionary.objects.count()

        self.assertLess(dictionaries_after, dictionaries_before)


class WordFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        cls.subject = Subject.objects.create(title="English", owner=cls.user)

        cls.dictionary = Dictionary.objects.create(
            title="Basic words", subject=cls.subject, words={"wojna": "war"}
        )

    def setUp(self):
        self.client.login(username="TestUser", password="test1234")

    def test_http_get_method_response_should_return_status_200(self):
        response = self.client.get(
            reverse(
                "dictionary:word_form", args=[self.subject.slug, self.dictionary.slug]
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_http_get_method_response_should_contains_dictionary_instance(self):
        response = self.client.get(
            reverse(
                "dictionary:word_form", args=[self.subject.slug, self.dictionary.slug]
            )
        )

        self.assertContains(response, self.dictionary)

    def test_http_post_method_response_should_return_status_302(self):
        response = self.client.post(
            reverse(
                "dictionary:word_form", args=[self.subject.slug, self.dictionary.slug]
            ),
            data={"word": "love", "definition": "miłość"},
        )

        self.assertEqual(response.status_code, 302)

    def test_http_post_method_when_invalid_data_provided_response_should_return_status_200(
        self,
    ):
        response = self.client.post(
            reverse(
                "dictionary:word_form", args=[self.subject.slug, self.dictionary.slug]
            ),
            data={"word": "war", "definition": "wojna"},
        )

        self.assertEqual(response.status_code, 200)

    def test_http_post_method_when_no_data_provided_response_should_return_status_200(
        self,
    ):
        response = self.client.post(
            reverse(
                "dictionary:word_form", args=[self.subject.slug, self.dictionary.slug]
            ),
            data={"word": "", "definition": ""},
        )

        self.assertEqual(response.status_code, 200)


class WordsManagementViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@email.com", username="TestUser", password="test1234"
        )

        cls.subject = Subject.objects.create(title="English", owner=cls.user)

        cls.dictionary = Dictionary.objects.create(
            title="Basic words", subject=cls.subject, words={"wojna": "war"}
        )

    def setUp(self):
        self.client.login(username="TestUser", password="test1234")

    def test_confirm_action_response_should_return_status_302(self):
        response = self.client.post(
            reverse("dictionary:confirm_changes", args=[self.dictionary.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_clear_list_action_response_should_return_status_302(self):
        response = self.client.post(
            reverse("dictionary:clear_list", args=[self.dictionary.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_refresh_list_action_response_should_return_status_302(self):
        response = self.client.post(
            reverse("dictionary:refresh_list", args=[self.dictionary.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_delete_action_response_should_return_status_302(self):
        response = self.client.post(
            reverse("dictionary:word_delete", args=[self.dictionary.id]),
            data={"definition": "wojna"},
        )

        self.assertEqual(response.status_code, 302)
