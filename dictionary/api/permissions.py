from rest_framework.permissions import BasePermission


class IsOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if self.__object_is_dictionary(obj):
            return obj.subject.owner == request.user
        return obj.owner == request.user

    def __object_is_dictionary(self, obj):
        return hasattr(obj, 'subject')
