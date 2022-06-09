from django.contrib import admin
from .models import Subject, Dictionary


@admin.register(Dictionary)
class DictionaryAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'owner']
    ordering = ['subject', 'title']
    list_filter = ['subject__owner']
    search_fields = ['subject', 'title']
    prepopulated_fields = {'slug': ['title']}

    @admin.display(description='właściciel')
    def owner(self, obj):
        return obj.subject.owner


class DictionaryInline(admin.StackedInline):
    model = Dictionary
    exclude = ['title', 'slug', 'description', 'words']
    extra = 0
    show_change_link = True


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'number_of_dicts']
    list_filter = ['owner']
    prepopulated_fields = {'slug': ['title']}

    @admin.display(description='liczba słowników')
    def number_of_dicts(self, obj):
        return obj.dicts.count()

    inlines = [DictionaryInline]
