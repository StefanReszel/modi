from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer, NestedHyperlinkedIdentityField


from ..models import Subject, Dictionary


class CustomUpdate:
    def update(self, instance, validated_data):
        update_fields = []

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            update_fields.append(attr)

        instance.save(update_fields=update_fields)
        return instance


class SubjectSerializer(CustomUpdate, serializers.HyperlinkedModelSerializer):
    dictionaries = serializers.HyperlinkedIdentityField(view_name='dictionary-list', lookup_url_kwarg='subject_pk')

    class Meta:
        model = Subject
        fields = ['url', 'id', 'slug', 'title', 'dictionaries']
        read_only_fields = ['url', 'id', 'slug']


class DictionarySerializer(CustomUpdate, NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'subject_pk': 'subject__id',
        }
    words = NestedHyperlinkedIdentityField(view_name='dictionary-words', parent_lookup_kwargs=parent_lookup_kwargs)

    class Meta:
        model = Dictionary
        # Check how field `subject` display in JSON document, append to `read_only_fields`.
        fields = ['url', 'id', 'slug', 'title', 'description', 'words']
        read_only_fields = ['url', 'id', 'slug']


class WordSerializer(serializers.Serializer):
    word = serializers.CharField(max_length=30)
    definition = serializers.CharField(max_length=60)


class WordToDeleteSerializer(serializers.Serializer):
    definition = serializers.CharField(max_length=60)
