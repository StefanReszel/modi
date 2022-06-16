from django.urls import path, include
from rest_framework_nested import routers
from . import views


subject_router = routers.SimpleRouter()
subject_router.register(r"subject", views.SubjectViewSet, basename="subject")

dictionary_router = routers.NestedSimpleRouter(
    subject_router, r"subject", lookup="subject"
)
dictionary_router.register(
    r"dictionary", views.DictionaryViewSet, basename="dictionary"
)

urlpatterns = [
    path("", include(subject_router.urls)),
    path("", include(dictionary_router.urls)),
]
