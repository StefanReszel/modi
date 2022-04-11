from django.urls import path
from . import views


app_name = 'dictionary'

urlpatterns = [
    path('', views.SubjectListView.as_view(
         template_name='subject/subject_list.html'), name='subject_list'),
    path('dodaj-temat/', views.SubjectCreateView.as_view(
         template_name='subject/subject_create_form.html'), name='subject_create'),
    path('<slug:subject_slug>/edytuj-temat/', views.SubjectUpdateView.as_view(
         template_name='subject/subject_update_form.html'), name='subject_update'),
    path('usun-temat/<int:pk>/', views.SubjectDeleteView.as_view(
         template_name='subject/subject_confirm_delete.html'), name='subject_delete'),

    path('<slug:subject_slug>/', views.DictionaryListView.as_view(
         template_name='dictionary/dictionary_list.html'), name='dict_list'),
    path('<slug:subject_slug>/dodaj-slownik/', views.DictionaryCreateView.as_view(
         template_name='dictionary/dictionary_create_form.html'), name='dict_create'),
    path('<slug:subject_slug>/<slug:dictionary_slug>/edytuj-slownik/', views.DictionaryUpdateView.as_view(
         template_name='dictionary/dictionary_update_form.html'), name='dict_update'),
    path('usun-slownik/<int:pk>/', views.DictionaryDeleteView.as_view(
         template_name='dictionary/dictionary_confirm_delete.html'), name='dict_delete'),

    path('<slug:subject_slug>/<slug:dictionary_slug>/slowa-i-definicje/', views.WordFormView.as_view(
         template_name='words_and_learning/word_form.html'), name='word_form'),

    path('delete-word/<int:dictionary_id>/', views.WordsManagementView.as_view(action='delete'), name='word_delete'),
    path('confirm-changes/<int:dictionary_id>/', views.WordsManagementView.as_view(action='confirm'), name='confirm_changes'),
    path('refresh-list/<int:dictionary_id>/', views.WordsManagementView.as_view(action='refresh'), name='refresh_list'),
    path('clear-list/<int:dictionary_id>/', views.WordsManagementView.as_view(action='clear'), name='clear_list'),

    path('<slug:subject_slug>/<slug:dictionary_slug>/', views.DictionaryDetailView.as_view(
         template_name='dictionary/dictionary_detail.html'), name='dict_detail'),
    path('<slug:subject_slug>/<slug:dictionary_slug>/nauka/', views.LearningView.as_view(
         template_name='words_and_learning/learning.html'), name='learning'),
    path('<slug:subject_slug>/<slug:dictionary_slug>/nauka/ukonczono/', views.LearningView.as_view(
         template_name='words_and_learning/complete.html'), name='complete'),
]
