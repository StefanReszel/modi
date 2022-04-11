from django import forms
from .models import Dictionary, Subject


class SearchForm(forms.Form):
    search = forms.CharField(max_length=30,
                             required=False,
                             widget=forms.TextInput(attrs={
                                 'type': 'search',
                                 'placeholder': 'Wpisz nazwę',
                                 'autofocus': True,
                                 'class': 'col-md-1 form-control w-100',
                                 }))


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Wpisz tytuł',
                'minlength': "3",
                'autofocus': True,
            }),
        }


class DictionaryForm(forms.ModelForm):
    class Meta:
        model = Dictionary
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nazwa',
                'minlength': "3",
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Opis - opcjonalny',
                'rows': '6',
            }),
        }


class WordForm(forms.Form):
    word = forms.CharField(max_length=30,
                           label='Słowo',
                           widget=forms.TextInput(attrs={
                               'class': 'form-control',
                               'placeholder': 'Słowo',
                               'autofocus': True,
                               }))
    definition = forms.CharField(max_length=60,
                                 label='Definicja',
                                 widget=forms.TextInput(attrs={
                                     'class': 'form-control',
                                     'placeholder': 'Definicja',
                                     }))
