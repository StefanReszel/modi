from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    FormView,
    View,
    TemplateView,
)
from django.db import IntegrityError
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from unidecode import unidecode

from accounts.views import LoginRequiredMixin
from .models import Dictionary, Subject
from .forms import SearchForm, SubjectForm, DictionaryForm, WordForm
from .words import Words, DuplicateError


class SubjectModelMixin:
    model = Subject


class SubjectModelFormMixin:
    form_class = SubjectForm

    def get_info_message(self):
        return "Temat o takiej lub podobnej nazwie najprawdopodobniej już istnieje."


class DictionaryModelMixin:
    model = Dictionary


class DictionaryModelFormMixin:
    form_class = DictionaryForm

    def get_info_message(self):
        return "Słownik o takiej lub podobnej nazwie najprawdopodobniej już istnieje."


class TemplateCreateSufixMixin:
    template_name_suffix = "_create_form"


class TemplateUpdateSufixMixin:
    template_name_suffix = "_update_form"


class GetSubjectObjectMixin:
    def get_subject_object(self):
        return get_object_or_404(
            Subject, slug=self.kwargs.get("subject_slug"), owner=self.request.user
        )


class GetDictionaryObjectMixin(GetSubjectObjectMixin):
    def get_object(self):
        return get_object_or_404(
            Dictionary,
            slug=self.kwargs.get("dictionary_slug"),
            subject=self.get_subject_object(),
        )


class CustomProcessFormMixin(GetSubjectObjectMixin):
    def form_valid(self, form):
        class_name = self.__class__.__name__

        if "Create" in class_name:
            self.object = form.save(commit=False)
            if "Subject" in class_name:
                self.object.owner = self.request.user
            if "Dictionary" in class_name:
                self.object.subject = self.get_subject_object()
        try:
            self.object.save()
            messages.success(self.request, self.get_success_message())
        except IntegrityError:
            if "Update" in class_name:
                self.__assign_object_from_db()

            messages.error(self.request, self.get_error_message())
            messages.info(self.request, self.get_info_message())

            return super().form_invalid(form)
        else:
            return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, self.get_error_message())
        return super().form_invalid(form)

    def __assign_object_from_db(self):
        """
        Without this, breadcrumbs in HTML template will render improperly.
        """
        self.object = self.get_object()

    def get_success_message(self):
        return "SUCCESS"

    def get_error_message(self):
        return "ERROR"

    def get_info_message(self):
        return "INFO"


class SearchMixin:
    def return_found_or_all(self, queryset):
        """
        Method handles search form. It's searching in slugs, which are based
        on titles, therefore, diacritics and capitals don't matter in lookups.
        It means 'ŁOŚ' is the same lookup such as 'los', so method will return
        all subjects or dictionaries with them in title.
        """
        self.query = self.request.GET.get("search")

        if not queryset:
            messages.info(self.request, self.get_empty_queryset_message())
            return queryset
        if self.query is not None:
            if self.query == "":
                messages.info(self.request, self.get_empty_form_field_message())
                return queryset
            self.extra_context = {"value": self.query}
            found = queryset.filter(slug__icontains=slugify(unidecode(self.query)))
            if not found:
                messages.info(self.request, self.get_not_found_message())
                return queryset
            return found
        return queryset

    def get_not_found_message(self):
        return "NOT FOUND"

    def get_empty_queryset_message(self):
        return "EMPTY QUERYSET"

    def get_empty_form_field_message(self):
        return "EMPTY FORM FIELD"


class CustomDeletionMixin:
    def post(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, self.get_success_message())
        return response

    def get_success_message(self):
        "SUCCESS"


class SubjectListView(LoginRequiredMixin, SubjectModelMixin, SearchMixin, ListView):
    def get_queryset(self):
        queryset = self.request.user.subjects.all()
        return self.return_found_or_all(queryset)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = SearchForm(initial={"search": self.query})
        return context

    def get_not_found_message(self):
        return "Temat o takiej nazwie nie istnieje."

    def get_empty_queryset_message(self):
        return "Nie dodano jeszcze tematów."

    def get_empty_form_field_message(self):
        return "Wpisz nazwę lub jej część, by znaleźć temat."


class SubjectCreateView(
    LoginRequiredMixin,
    SubjectModelMixin,
    SubjectModelFormMixin,
    TemplateCreateSufixMixin,
    CustomProcessFormMixin,
    CreateView,
):
    def get_success_message(self):
        return "Dodawanie tematu zakończyło się pomyślnie."

    def get_error_message(self):
        return "Dodawanie tematu się nie powiodło."


class SubjectUpdateView(
    LoginRequiredMixin,
    SubjectModelFormMixin,
    TemplateUpdateSufixMixin,
    CustomProcessFormMixin,
    UpdateView,
):
    def get_object(self):
        return self.get_subject_object()

    def get_success_message(self):
        return "Edycja tematu zakończyła się pomyślnie."

    def get_error_message(self):
        return "Edycja tematu się nie powiodła."


class SubjectDeleteView(
    LoginRequiredMixin, SubjectModelMixin, CustomDeletionMixin, DeleteView
):
    success_url = reverse_lazy("dictionary:subject_list")

    def get_success_message(self):
        return "Temat usunięto pomyślnie."


class DictionaryListView(
    LoginRequiredMixin, SearchMixin, GetSubjectObjectMixin, ListView
):
    def get_queryset(self):
        self.subject = self.get_subject_object()
        queryset = self.subject.dicts.all()
        return self.return_found_or_all(queryset)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = SearchForm(initial={"search": self.query})
        context["subject"] = self.subject
        return context

    def get_not_found_message(self):
        return "Słownik o takiej nazwie nie istnieje."

    def get_empty_queryset_message(self):
        return "Nie dodano jeszcze słowników."

    def get_empty_form_field_message(self):
        return "Wpisz nazwę lub jej część, by znaleźć słownik."


class DictionaryCreateView(
    LoginRequiredMixin,
    DictionaryModelMixin,
    DictionaryModelFormMixin,
    TemplateCreateSufixMixin,
    CustomProcessFormMixin,
    CreateView,
):
    def get_success_url(self):
        add_word_message = "Dodaj teraz jakieś słowa i definicje."
        messages.info(self.request, add_word_message)
        return reverse_lazy(
            "dictionary:word_form", args=[self.object.subject.slug, self.object.slug]
        )

    def get_context_data(self, **kwargs):
        return super().get_context_data(subject=self.get_subject_object(), **kwargs)

    def get_success_message(self):
        return "Dodawanie słownika zakończyło się pomyślnie."

    def get_error_message(self):
        return "Dodawanie słownika się nie powiodło."


class DictionaryDetailView(LoginRequiredMixin, GetDictionaryObjectMixin, DetailView):
    pass


class DictionaryUpdateView(
    LoginRequiredMixin,
    DictionaryModelFormMixin,
    GetDictionaryObjectMixin,
    TemplateUpdateSufixMixin,
    CustomProcessFormMixin,
    UpdateView,
):
    def get_success_message(self):
        return "Edycja słownika zakończyła się pomyślnie."

    def get_error_message(self):
        return "Edycja słownika się nie powiodła."


class DictionaryDeleteView(
    LoginRequiredMixin, DictionaryModelMixin, CustomDeletionMixin, DeleteView
):
    def get_success_url(self):
        return reverse_lazy("dictionary:dict_list", args=[self.object.subject.slug])

    def get_context_data(self, **kwargs):
        return super().get_context_data(subject=self.object.subject, **kwargs)

    def get_success_message(self):
        return "Słownik usunięto pomyślnie."


class WordFormView(LoginRequiredMixin, GetDictionaryObjectMixin, FormView):
    form_class = WordForm
    template_name = "dictionary/word_form.html"

    def get_success_url(self):
        return reverse_lazy(
            "dictionary:word_form",
            args=[self.dictionary.subject.slug, self.dictionary.slug],
        )

    def get_context_data(self, **kwargs):
        if not hasattr(self, "dictionary"):
            self.dictionary = self.get_object()
            self.words = Words(self.request, self.dictionary)
        return super().get_context_data(
            dictionary=self.dictionary, words=self.words.get_words()
        )

    def form_valid(self, form):
        cd = form.cleaned_data
        self.dictionary = self.get_object()
        self.words = Words(self.request, self.dictionary)

        try:
            self.words.add_word(word=cd["word"], definition=cd["definition"])
        except DuplicateError:
            messages.error(self.request, "Definicja o takiej treści już istnieje.")
            return super().form_invalid(form)
        else:
            return super().form_valid(form)


class WordsManagementView(LoginRequiredMixin, View):
    """
    This view, in regard to `self.action`, performs appropriate method of `Words` instance.

    `action` is passing to URLconfs, in module `dictionary.urls`.
    """

    action = None

    def post(self, request, *args, **kwargs):
        dictionary = get_object_or_404(Dictionary, id=kwargs.get("dictionary_id"))
        words = Words(request, dictionary)
        actions = {
            "clear": words.clear_list,
            "refresh": words.refresh_list,
        }
        if self.action == "confirm":
            words.save_to_db()
            return redirect(
                "dictionary:dict_detail", dictionary.subject.slug, dictionary.slug
            )
        elif self.action == "delete":
            definition = self.request.POST["definition"]
            words.remove_word(definition)
        else:
            actions[self.action]()
        return redirect(
            "dictionary:word_form", dictionary.subject.slug, dictionary.slug
        )


class LearningView(LoginRequiredMixin, GetDictionaryObjectMixin, TemplateView):
    def get_context_data(self, **kwargs):
        return super().get_context_data(dictionary=self.get_object())
