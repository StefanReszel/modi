from rest_framework import viewsets, permissions, serializers, status, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action

from django.db import IntegrityError
from django.utils.text import slugify
from unidecode import unidecode

from .serializers import SubjectSerializer, DictionarySerializer, WordSerializer, WordToDeleteSerializer
from .permissions import IsOwnerPermission
from ..models import Subject
from ..words import Words, DuplicateError, DefinitionDoesNotExist


class IsAuthenticatedOwnerMixin:
    permission_classes = [permissions.IsAuthenticated, IsOwnerPermission]


class SearchMixin:
    def return_found_or_all(self, queryset):
        """
        This method looks up in slugs, which are based on titles,
        therefore, diacritics and capitals don't matter in lookups.
        It means 'ŁOŚ' is the same lookup such as 'los', so method
        will return all subjects or dictionaries with them in title.
        """
        query = self.request.query_params.get('search')
        if query:
            if queryset:
                found = queryset.filter(
                    slug__icontains=slugify(unidecode(query)))
                if not found:
                    return queryset
                return found
        return queryset


class SubjectViewSet(IsAuthenticatedOwnerMixin, SearchMixin, viewsets.ModelViewSet):
    serializer_class = SubjectSerializer

    def get_queryset(self):
        queryset = self.request.user.subjects.all()
        return self.return_found_or_all(queryset)

    def perform_create(self, serializer):
        try:
            serializer.save(owner=self.request.user)
        except IntegrityError:
            raise serializers.ValidationError(["Dodawanie tematu się nie powiodło.",
                  "Temat o takiej lub podobnej nazwie najprawdopodobniej już istnieje."])


class DictionaryViewSet(IsAuthenticatedOwnerMixin, SearchMixin, viewsets.ModelViewSet):
    serializer_class = DictionarySerializer

    def dispatch(self, request, *args, **kwargs):
        subject_id = self.kwargs.get('subject_pk')
        try:
            self.subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            self.subject = None
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.subject is None:
            raise exceptions.NotFound({"detail": "Nie znaleziono."})
        queryset = self.subject.dicts.all()
        return self.return_found_or_all(queryset)

    def perform_create(self, serializer):
        try:
            serializer.save(subject=self.subject)
        except IntegrityError:
            raise serializers.ValidationError(["Dodawanie słownika się nie powiodło.",
                  "Słownik o takiej lub podobnej nazwie najprawdopodobniej już istnieje."])

    @action(detail=True)
    def words(self, request, *args, **kwargs):
        """
        Return words from `Dictionary` object.
        """
        dictionary = self.get_object()
        return Response(data=dictionary.words)

    @action(detail=True, url_path='words/edit')
    def edit_words(self, request, *args, **kwargs):
        """
        Returns words from session.
        """
        words = Words(request, self.get_object())
        return Response(data=dict(words.get_words()))

    @edit_words.mapping.post
    def save_words(self, request, *args, **kwargs):
        """
        Saves words to database.
        """
        words = Words(request, self.get_object())
        words.save_to_db()
        return Response(data={'status': 'OK'})

    @edit_words.mapping.put
    def add_word(self, request, *args, **kwargs):
        serializer = WordSerializer(data=request.data)
        if serializer.is_valid():
            words = Words(request, self.get_object())
            try:
                words.add_word(serializer.validated_data['word'],
                               serializer.validated_data['definition'])
            except DuplicateError as error:
                raise serializers.ValidationError(error)
            return Response(data=dict(words.get_words()), status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @edit_words.mapping.delete
    def delete_word(self, request, *args, **kwargs):
        words = Words(request, self.get_object())
        serializer = WordToDeleteSerializer(data=request.data)
        serializer.is_valid()
        try:
            words.remove_word(serializer.data.get('definition'))
        except DefinitionDoesNotExist as error:
            raise serializers.ValidationError(error)
        return Response(data=dict(words.get_words()))

    @action(detail=True, url_path='words/edit/refresh', methods=['POST'])
    def refresh_words(self, request, *args, **kwargs):
        """
        Copies words from `Dictionary` object to session.
        """
        words = Words(request, self.get_object())
        words.refresh_list()
        return Response(data=dict(words.get_words()))
