from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from ..permissions import *
from ..models import AudioFiles, Content, VideoFiles, User
from ..serializers import *
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.conf import settings
import os
import telegram
from settings.settings import *


@api_view(['POST'])
def send_audio_to_telegram(request, audio_id):
    # Получаем объект аудиофайла или возвращаем 404, если он не существует
    audio = get_object_or_404(AudioFiles, pk=audio_id)

    # Получаем данные аудиофайла
    audio_name = audio.name_audio
    creator = audio.creator_audio
    audio_file = audio.audio_file

    # Создаем сообщение для отправки в Telegram
    message = f"Название: {audio_name}\nСоздатель: {creator}"

    # Инициализируем бота Telegram
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)  # Замените на ваш токен бота

    # Отправляем сообщение в чат бота
    bot.send_message(chat_id=ADMIN_TELEGRAM_CHAT_ID, text=message)

    # Отправляем аудиофайл в чат бота
    with open(audio_file.path, 'rb') as audio_file:
        bot.send_audio(chat_id=ADMIN_TELEGRAM_CHAT_ID, audio=audio_file)

    # Возвращаем ответ об успешной отправке
    return Response({'message': 'Информация и аудиофайл отправлены в Telegram'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsTeacherOrReadOnly])
def audio_files_list(request):
    user = request.user
    if request.method == 'GET':
        if user.role == 'Teacher':
            # Проверяем, что пользователь просматривает только свои аудиофайлы
            audio_files = AudioFiles.objects.filter(user=user)
        else:
            # Для студентов показываем аудиофайлы, доступные их группе
            # Проверяем наличие у пользователя учебной группы
            if not user.group:
                raise PermissionDenied("Вы не привязаны к учебной группе.")
            audio_files = AudioFiles.objects.filter(
                group_educational=user.group)

        audio_data = []
        for audio in audio_files:
            audio_path = audio.audio_file.path

            # Размер файла в мегабайтах
            size_in_mb = round(audio.audio_file.size / (1024 * 1024), 2)
            audio.save()

            content_serializer = ContentSerializer(audio.content_id)
            content_data = content_serializer.data

            video_serializer = VideoFilesSerializer(audio.video_id)
            video_data = video_serializer.data

            # Формирование данных для JsonResponse
            audio_info = {
                'id': audio.id,
                'name_audio': audio.name_audio,
                'creator_audio': audio.creator_audio,
                'data_create': audio.data_create,
                'file_path': audio.file_path,
                'group_educational': audio.group_educational,
                'audio_file': {
                    'url': audio.audio_file.url,
                    'name': str(audio.audio_file),  # Имя файла
                    'size': f"{size_in_mb} MB",  # Размер файла в мегабайтах
                    'format': audio.format,
                },
                'content': content_data,
                'videofile': video_data
            }
            audio_data.append(audio_info)

        return JsonResponse(audio_data, safe=False)

    elif request.method == 'POST':
        # Проверяем, является ли пользователь преподавателем
        if user.role != 'Teacher':
            raise PermissionDenied(
                "Только преподаватели могут добавлять аудиофайлы.")

        # Получаем номер учебной группы из запроса
        group_educational = request.data.get('group_educational')
        if not group_educational:
            return Response({'error': 'Укажите учебную группу.'}, status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.filter(role='Student', group=group_educational).exists():
            return Response({'error': 'Указанная учебная группа не существует.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка учебной группы контента и видеофайла
        content_id = request.data.get('content_id')
        video_id = request.data.get('video_id')

        # Проверяем, существует ли контент с переданным content_id
        try:
            content = Content.objects.get(pk=content_id)
        except Content.DoesNotExist:
            return Response({'error': 'Invalid content_id. Content does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, существует ли видео с переданным video_id
        try:
            video = VideoFiles.objects.get(pk=video_id)
        except VideoFiles.DoesNotExist:
            return Response({'error': 'Invalid video_id. Video does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что контент принадлежит текущему пользователю
        if content.user != user:
            raise PermissionDenied(
                "Вы можете добавлять аудиофайлы только для своего контента.")

        # Проверяем, что видео принадлежит текущему пользователю
        if video.user != user:
            raise PermissionDenied(
                "Вы можете добавлять аудиофайлы только для своего видеофайла.")

        # Проверка соответствия учебных групп
        if group_educational != content.group_educational or group_educational != video.group_educational:
            return Response({'error': 'Учебная группа аудиофайла должна соответствовать учебной группе контента и видеофайла.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Добавляем пользователя в данные для сохранения
        request.data['user'] = user.id

        # Сериализатор для проверки данных
        serializer = AudioFilesSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            audio_file = request.FILES.get('audio_file')
            if not audio_file:
                return Response({'error': 'Audio file is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Проверка формата файла
            allowed_formats = ['mp3', 'aac', 'wav', 'flac', 'dsd']
            file_extension = audio_file.name.split(
                '.')[-1].lower() if '.' in audio_file.name else None
            if file_extension not in allowed_formats:
                return Response({'error': f'Invalid audio file format. Allowed formats: {", ".join(allowed_formats)}.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Создание экземпляра AudioFiles
            audio_instance = AudioFiles.objects.create(
                name_audio=request.data.get('name_audio'),
                creator_audio=request.data.get('creator_audio'),
                data_create=request.data.get('data_create'),
                file_path=request.data.get('file_path'),
                format=request.data.get('format'),
                content_id=content,
                video_id=video,
                user=user,
                group_educational=group_educational,
            )
            audio_instance.audio_file = audio_file
            audio_instance.save()

            return Response(AudioFilesSerializer(audio_instance).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsTeacherAndOwnerOrReadOnly])
def update_audio_file(request, audio_id):
    if request.method == 'PUT':
        audio = get_object_or_404(AudioFiles, pk=audio_id)
        if audio.user != request.user:
            return Response({'error': 'Вы не имеете прав на редактирование этого аудиофайла.'}, status=status.HTTP_403_FORBIDDEN)

        # Проверяем существование указанной учебной группы в модели User
        group_educational = request.data.get('group_educational')
        if not User.objects.filter(role='Student', group=group_educational).exists():
            return Response({'error': 'Указанная учебная группа не существует'}, status=status.HTTP_400_BAD_REQUEST)

        if 'user' in request.data:
            del request.data['user']

        serializer = AudioFilesSerializer(
            audio, data=request.data, partial=True)
        if serializer.is_valid():
            audio_file = request.FILES.get('audio_file')
            if audio_file:
                # Если загружен новый аудиофайл, сохраняем его
                audio.audio_file.delete()  # Удаляем старый файл
                audio.audio_file = audio_file  # Присваиваем новый файл
            serializer.save(group_educational=group_educational)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsTeacherAndOwnerOrReadOnly])
def audio_files_delete(request, audio_id):
    if request.method == 'DELETE':
        audio = get_object_or_404(AudioFiles, pk=audio_id)

        # Проверяем права доступа
        if audio.user != request.user:
            return Response({'error': 'Вы не имеете прав на удаление этого аудиофайла.'}, status=status.HTTP_403_FORBIDDEN)

        # Удаляем запись из базы данных
        audio.delete()

        # Удаляем файл из файловой системы
        audio_file_path = os.path.join(
            settings.MEDIA_ROOT, audio.audio_file.name)
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

        return Response({'message': 'Аудиофайл успешно удален'}, status=status.HTTP_204_NO_CONTENT)
