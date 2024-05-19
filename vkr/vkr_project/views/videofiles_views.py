from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from settings.settings import *
from rest_framework import status
import os
import shutil
import time
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
import json
from ..permissions import *
from ..models import Content, VideoFiles, User
from ..serializers import VideoFilesSerializer, ContentSerializer
from django.core.files.base import ContentFile
from telegram import Bot


def archive_file(file_path):
    archive_path = file_path + '.zip'
    shutil.make_archive(file_path, 'zip', os.path.dirname(
        file_path), os.path.basename(file_path))
    return archive_path


def send_video_to_telegram(video_data):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Формируем сообщение для отправки
    message = (
        f"Название: {video_data['title_video']}\n"
        f"Описание: {video_data['description']}\n"
        f"Формат: {video_data['format']}\n"
        f"Учебная группа: {video_data['group_educational']}\n"
        f"Преподаватель: {video_data['content']['user']}\n"
    )

    # Отправляем сообщение в Telegram бот
    bot.send_message(chat_id=ADMIN_TELEGRAM_CHAT_ID, text=message)

    archive_path = archive_file(video_data['file_path'])

    # Отправляем архив как документ в Telegram бот
    with open(archive_path, 'rb') as video_file:
        bot.send_document(chat_id=ADMIN_TELEGRAM_CHAT_ID,
                          document=video_file, caption=video_data['title_video'])

    # Удаляем временный архив после отправки
    os.remove(archive_path)


@permission_classes([IsTeacherOrReadOnly])
@api_view(['POST'])
def send_video_to_telegram_view(request, video_id):
    # Получаем видеофайл по его идентификатору или возвращаем ошибку 404, если видео не найдено
    video = get_object_or_404(VideoFiles, pk=video_id)

    # Проверка существования файла на файловой системе
    if not os.path.exists(video.video_file.path):
        return Response({'error': 'Видео файл не найден на сервере.'}, status=status.HTTP_404_NOT_FOUND)

    # Создаем словарь с данными о видеофайле
    video_data = {
        'title_video': video.title_video,
        'description': video.description,
        'file_path': video.video_file.path,  # Абсолютный путь к видеофайлу
        'file_name': video.video_file.name,  # Имя файла
        'file_size': video.video_file.size,
        'file_url': video.video_file.url,
        'format': video.format,
        'content': {
            'id': video.content_id.id,
            'title': video.content_id.title,
            'group_educational': video.content_id.group_educational,
            'user': video.content_id.user.username,
        },
        'group_educational': video.group_educational,
    }

    send_video_to_telegram(video_data)

    return Response({'status': 'Видео отправлено в Telegram'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def video_files_list(request):
    user = request.user
    if request.method == 'GET':
        if user.role == 'Teacher':
            # Проверяем, что пользователь просматривает только свои видеофайлы
            video_files = VideoFiles.objects.filter(user=user)
        else:
            # Для студентов показываем видеофайлы, доступные их группе
            # Проверяем наличие у пользователя учебной группы
            if not user.group:
                raise PermissionDenied("Вы не привязаны к учебной группе.")
            video_files = VideoFiles.objects.filter(
                group_educational=user.group)

        video_data = []
        for video in video_files:
            video_path = video.video_file.path

            # Размер файла в мегабайтах
            size_in_mb = round(video.video_file.size / (1024 * 1024), 2)
            video.save()

            # Сериализация объекта Content
            content_serializer = ContentSerializer(video.content_id)
            content_data = content_serializer.data

            # Формирование данных для JsonResponse
            video_info = {
                'id': video.id,
                'title_video': video.title_video,
                'description': video.description,
                'file_path': video.file_path,
                'group_educational': video.group_educational,
                'video_file': {
                    'url': video.video_file.url,
                    'name': str(video.video_file),  # Имя файла
                    'size': f"{size_in_mb} MB",  # Размер файла в мегабайтах
                    'format': video.format,
                },
                'content': content_data,
            }
            video_data.append(video_info)

        return JsonResponse(video_data, safe=False)

    elif request.method == 'POST':
        # Проверяем, является ли пользователь преподавателем
        if user.role != 'Teacher':
            raise PermissionDenied(
                "Только преподаватели могут добавлять видеофайлы.")

        # Получаем номер учебной группы из запроса
        group_educational = request.data.get('group_educational')
        if not group_educational:
            return Response({'error': 'Укажите учебную группу.'}, status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.filter(role='Student', group=group_educational).exists():
            return Response({'error': 'Указанная учебная группа не существует.'}, status=status.HTTP_400_BAD_REQUEST)

        # Добавляем пользователя в данные для сохранения
        request.data['user'] = user.id
        serializer = VideoFilesSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            video_file = request.FILES.get('video_file')
            if not video_file:
                return Response({'error': 'Video file is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Проверка формата файла
            allowed_formats = ['mp4', 'mkv']
            file_extension = video_file.name.split(
                '.')[-1].lower() if '.' in video_file.name else None
            if file_extension not in allowed_formats:
                return Response({'error': f'Invalid video file format. Allowed formats: {", ".join(allowed_formats)}.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, существует ли контент с переданным content_id
            content_id = request.data.get('content_id')
            try:
                content = Content.objects.get(pk=content_id)
            except Content.DoesNotExist:
                return Response({'error': 'Invalid content_id. Content does not exist.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, что контент принадлежит текущему пользователю
            if content.user != user:
                raise PermissionDenied(
                    "Вы можете добавлять видеофайлы только для своего контента.")

            # Проверяем, совпадает ли учебная группа контента и видеофайла
            if content.group_educational != group_educational:
                return Response({'error': 'Учебная группа видеофайла не совпадает с учебной группой контента.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Сохранение файла в модели VideoFiles
            serializer.save(user=user, video_file=video_file,
                            content_id=content)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsTeacherAndOwnerOrReadOnly])
def update_video_file(request, video_id):
    if request.method == 'PUT':
        video = get_object_or_404(VideoFiles, pk=video_id)

        if video.user != request.user:
            return Response({'error': 'Вы не имеете прав на редактирование этого видеофайла.'}, status=status.HTTP_403_FORBIDDEN)

        # Проверяем существование указанной учебной группы в модели User
        group_educational = request.data.get('group_educational')
        if not User.objects.filter(role='Student', group=group_educational).exists():
            return Response({'error': 'Указанная учебная группа не существует'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что группа видеофайла соответствует группе контента
        if group_educational != video.content_id.group_educational:
            return Response({'error': 'Учебная группа видеофайла должна соответствовать учебной группе контента. Для изменения учебной группы, сначала измените учебную группу контента.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = VideoFilesSerializer(
            video, data=request.data, partial=True)
        if serializer.is_valid():
            video_file = request.FILES.get('video_file')
            if video_file:
                # Проверяем формат файла
                allowed_formats = ['mp4', 'mkv']
                file_extension = video_file.name.split(
                    '.')[-1].lower() if '.' in video_file.name else None
                if file_extension not in allowed_formats:
                    return Response({'error': f'Invalid video file format. Allowed formats: {", ".join(allowed_formats)}.'},
                                    status=status.HTTP_400_BAD_REQUEST)

            # Добавляем пользователя в данные для сохранения
            request.data['user'] = request.user.id

            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsTeacherAndOwnerOrReadOnly])
def video_files_delete(request, video_id):
    # Получаем текущего пользователя
    user = request.user
    # Получаем видеофайл для удаления
    videofile = get_object_or_404(VideoFiles, pk=video_id)
    # Проверяем, принадлежит ли видеофайл текущему пользователю (преподавателю)
    if videofile.user != user:
        return Response({'error': 'Вы не имеете прав на удаление этого видеофайла.'}, status=status.HTTP_403_FORBIDDEN)

    # Удаляем файл с файловой системы
    if os.path.exists(videofile.video_file.path):
        os.remove(videofile.video_file.path)

    # Удаляем запись из БД
    videofile.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)
