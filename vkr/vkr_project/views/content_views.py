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
from ..models import *
from ..serializers import *



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

    elif request.method == 'POST':
        serializer = ContentSerializer(data=request.data)
        if serializer.is_valid():
            # Передаем текущего пользователя
            serializer.save(user=request.user)
            content = serializer.instance
            if 'content_file' in request.FILES:
                content.content_file = request.FILES['content_file']
                content.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
