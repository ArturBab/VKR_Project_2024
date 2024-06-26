from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from django.core.files import File
from io import BytesIO
from settings.settings import *
from rest_framework import status
from django.shortcuts import get_object_or_404
import json
from ..permissions import *
from rest_framework.permissions import IsAuthenticated
from ..models import Content, User
from ..serializers import ContentSerializer
import telegram


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrReadOnly])
def telegram_content_detail(request, content_id):
    content = get_object_or_404(Content, pk=content_id)
    # Отправка текстовых данных в Телеграм
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    chat_id = ADMIN_TELEGRAM_CHAT_ID
    message = f"Название: {content.title}\nПуть к файлу: {content.file_path}\nУчебная группа: {content.group_educational}\nПреподаватель: {content.user}"
    bot.send_message(chat_id=chat_id, text=message)

    # Отправка файла в Телеграм
    file_bytes = BytesIO()
    content.content_file.open('rb')
    file_bytes.write(content.content_file.read())
    file_bytes.seek(0)
    bot.send_document(chat_id=chat_id, document=file_bytes,
                      filename=content.content_file.name)

    return HttpResponse("Data sent to Telegram bot")


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
        serializer = ContentSerializer(data=request.data)
    if serializer.is_valid():
        # Если пользователь преподаватель, то устанавливаем его в качестве автора контента
        if user.role == 'Teacher':
            # Получаем номер учебной группы из запроса
            group_educational = serializer.validated_data.get(
                'group_educational')
            # Проверяем существование учебной группы в модели User
            if not User.objects.filter(role='Student', group=group_educational).exists():
                return Response({'error': 'Указанная учебная группа не существует.'}, status=status.HTTP_400_BAD_REQUEST)
            # Сохраняем контент
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Только преподаватель может добавлять контент.'}, status=status.HTTP_403_FORBIDDEN)
    else:
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

        # Продолжаем обработку запроса только если контент принадлежит текущему пользователю
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

        # Продолжаем удаление только если контент принадлежит текущему пользователю
        content.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)
