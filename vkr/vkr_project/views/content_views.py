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
            content = Content.objects.filter(user__role='Teacher')
        elif user.role == 'Teacher':
            # Для преподавателя показываем его собственный контент
            content = Content.objects.filter(user=user)
        else:
            # Для других пользователей пока не показываем контент
            content = Content.objects.none()

        serializer = ContentSerializer(content, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        # Проверяем наличие поля group в запросе
        group_number = request.data.get('group')
        if not group_number:
            return Response({'error': 'Укажите номер учебной группы студентов.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем роль пользователя
        if user.role == 'Student':
            # Получаем номер учебной группы текущего пользователя
            user_group_number = user.group
            # Добавим отладочный вывод
            print("User's group number:", user_group_number)
            if not user_group_number:
                return Response({'error': 'Укажите номер учебной группы студентов.'}, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем существование учебной группы по ее номеру
            if not User.objects.filter(role='Student', group=user_group_number).exists():
                # Добавим отладочный вывод
                print("Group does not exist:", user_group_number)
                return Response({'error': 'Указанная учебная группа не существует.'}, status=status.HTTP_400_BAD_REQUEST)

            # Добавим отладочный вывод
            print("Group exists:", user_group_number)

        # Проверяем существование указанной учебной группы
        if not User.objects.filter(role='Student', group=group_number).exists():
            # Добавим отладочный вывод
            print("Group does not exist:", group_number)
            return Response({'error': 'Указанная учебная группа не существует.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ваш текущий код для обработки POST запроса
        request.data['user'] = request.user.id
        serializer = ContentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            content = serializer.instance
            if 'content_file' in request.FILES:
                content.content_file = request.FILES['content_file']
                content.save()

            # Получаем информацию о предоставленной группе
            group_info = group_number or user.group

            # Обновляем сериализатор для включения информации о группе
            serialized_data = serializer.data
            serialized_data['group'] = group_info

            return Response(serialized_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsTeacherAndOwnerOrReadOnly])
def update_content(request, content_id):
    # Получаем текущего пользователя
    user = request.user

    if request.method == 'PUT':
        # Получаем контент для обновления
        content = get_object_or_404(Content, pk=content_id)

        # Проверяем, принадлежит ли контент текущему пользователю (преподавателю)
        if content.user != user:
            return Response({'error': 'Вы не имеете прав на редактирование этого контента'}, status=status.HTTP_403_FORBIDDEN)

        # Продолжаем обработку запроса только если контент принадлежит текущему пользователю
        request.data['user'] = request.user.id
        serializer = ContentSerializer(content, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
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

        # Продолжаем удаление только если контент принадлежит текущему пользователю
        content.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)
