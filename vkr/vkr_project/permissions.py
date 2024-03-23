from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsTeacherOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role == 'Teacher':
            return True
        return request.method in ['GET']


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user == obj.user:
            return True
        return request.method in ['GET']


class IsTeacherAndOwnerOrReadOnly(BasePermission):
    """
    Позволяет только учителю редактировать или удалять свои файлы.
    """

    def has_permission(self, request, view):
        # Проверяем, является ли пользователь учителем
        return request.user.role == 'Teacher'

    def has_object_permission(self, request, view, obj):
        # Разрешить GET, HEAD или OPTIONS запросы для любого пользователя
        if request.method in SAFE_METHODS:
            return True
        # Разрешить редактирование или удаление только владельцу объекта
        return obj.user == request.user
