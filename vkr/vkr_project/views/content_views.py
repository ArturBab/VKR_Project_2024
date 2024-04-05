from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import os
import time
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
import json
from ..permissions import *
from ..models import Content, User
from ..serializers import ContentSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsTeacherOrReadOnly])
def content_list(request):
    # Получаем авторизованного пользователя
    user = request.user
    if request.method == 'GET':
        # Получаем контент, доступный для просмотра авторизованному пользователю
        if user.role == 'Student':
            # Для студента показываем только контент, доступный его группе
            content = Content.objects.filter(group_educational=user.group)
        elif user.role == 'Teacher':
            # Для преподавателя показываем его собственный контент
            content = Content.objects.filter(user=user)
        else:
            # Для других пользователей пока не показываем контент
            content = Content.objects.none()

        serializer = ContentSerializer(content, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        # Получаем номер учебной группы из запроса
        group_educational = request.data.get('group_educational')

        # Проверяем наличие номера учебной группы
        if not group_educational:
            return Response({'error': 'Укажите учебную группу.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем существование учебной группы в модели User
        if not User.objects.filter(role='Student', group=group_educational).exists():
            return Response({'error': 'Указанная учебная группа не существует.'}, status=status.HTTP_400_BAD_REQUEST)

        request.data['user'] = request.user.id
        serializer = ContentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user,
                            group_educational=group_educational)
            content = serializer.instance
            if 'content_file' in request.FILES:
                content.content_file = request.FILES['content_file']
                content.save()

            # Обновляем сериализатор для включения информации о группе
            serialized_data = serializer.data
            serialized_data['group_educational'] = group_educational

            return Response(serialized_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsTeacherAndOwnerOrReadOnly])
def update_content(request, content_id):
    if request.method == 'PUT':
        # Получаем контент для обновления
        content = get_object_or_404(Content, pk=content_id)

        # Проверяем, принадлежит ли контент текущему пользователю (преподавателю)
        if content.user != request.user:
            return Response({'error': 'Вы не имеете прав на редактирование этого контента'}, status=status.HTTP_403_FORBIDDEN)

        # Проверяем существование указанной учебной группы в модели User
        group_educational = request.data.get('group_educational')
        if not User.objects.filter(role='Student', group=group_educational).exists():
            return Response({'error': 'Указанная учебная группа не существует'}, status=status.HTTP_400_BAD_REQUEST)

        # Удаляем поле 'user' из данных запроса, если оно есть
        if 'user' in request.data:
            del request.data['user']

        serializer = ContentSerializer(content, data=request.data)
        if serializer.is_valid():
            # Устанавливаем текущего пользователя как владельца контента
            serializer.validated_data['user'] = request.user
            # Обновляем поле group_educational
            serializer.save(group_educational=group_educational)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated, IsTeacherAndOwnerOrReadOnly])
def content_delete(request, content_id):
    # Получаем текущего пользователя
    user = request.user
    if request.method == 'DELETE':
        # Получаем контент для удаления
        content = get_object_or_404(Content, pk=content_id)

        # Проверяем, принадлежит ли контент текущему пользователю (преподавателю)
        if content.user != user:
            return Response({'error': 'Вы не имеете прав на удаление этого контента'}, status=status.HTTP_403_FORBIDDEN)

        content.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)
