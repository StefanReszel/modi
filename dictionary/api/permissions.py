from rest_framework.permissions import BasePermission


class IsOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        # check whether object is `Dictionary`...
        if hasattr(obj, 'subject'):
            return obj.subject.owner == request.user
        # if not, object is `Subject`
        return obj.owner == request.user
