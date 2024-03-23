from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import os
import time
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
import json
from .permissions import *
from .models import *
from .serializers import *



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


@api_view(['GET', 'POST'])
def audio_files_list(request):
    if request.method == 'GET':
        audio_files = AudioFiles.objects.all()
        audio_data = []
        for audio in audio_files:
            audio_path = audio.audio_file.path

            # Измерение пропускной способности
            start_time = time.time()
            with open(audio_path, 'rb') as audio_file:
                response = HttpResponse(audio_file, content_type='audio/mp3')

            end_time = time.time()

            # Вычисление времени передачи
            duration = end_time - start_time

            # Размер файла в мегабайтах
            size_in_mb = round(audio.audio_file.size / (1024 * 1024), 2)

            # Подсчет пропускной способности в Mbps
            file_size_in_bytes = os.path.getsize(audio_path)
            bandwidth = (file_size_in_bytes * 8) / \
                (duration * 1000000)  # Переводим в Mbps

            # Обновление поля пропускной способности в объекте AudioFiles
            audio.bandwidth = bandwidth
            bandwidth_in_mbps = round(bandwidth, 2)
            audio.save()

            # Формирование данных для JsonResponse
            audio_info = {
                'id': audio.id,
                'name_audio': audio.name_audio,
                'creator_audio': audio.name_audio,
                'data_create': audio.name_audio,
                'file_path': audio.file_path,
                'audio_file': {
                    'url': audio.audio_file.url,
                    'name': str(audio.audio_file),  # Имя файла
                    'size': f"{size_in_mb} MB",  # Размер файла в мегабайтах
                    'format': audio.format,
                    'bandwidth_audio_file': f"{bandwidth_in_mbps} Mbps"
                }
            }
            audio_data.append(audio_info)

        return JsonResponse(audio_data, safe=False)

    elif request.method == 'POST':
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
            print(f'File extension: {file_extension}')
            print(f'Allowed formats: {allowed_formats}')
            if file_extension not in allowed_formats:
                print('Invalid format!')
                return Response({'error': f'Invalid audio file format. Allowed formats: {", ".join(allowed_formats)}.'},
                                status=status.HTTP_400_BAD_REQUEST)

            content_id = request.data.get('content_id')
            video_id = request.data.get('video_id')

            # Проверяем, существует ли контент с переданным content_id
            try:
                content = Content.objects.get(pk=content_id)
            except Content.DoesNotExist:
                return Response({'error': 'Invalid content_id. Content does not exist.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, существует ли видео с переданным video_id
            try:
                video = VideoFiles.objects.get(pk=video_id)
            except VideoFiles.DoesNotExist:
                return Response({'error': 'Invalid video_id. Video does not exist.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Сохранение файла в модели Audio
            serializer.save(audio_file=audio_file,
                            content_id=content, video_id=video)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Функции для работы с аудио-файлами
@api_view(['PUT'])
def update_audio_file(request, audio_id):
    audio = get_object_or_404(AudioFiles, pk=audio_id)

    if request.method == 'PUT':
        serializer = AudioFilesSerializer(audio, data=request.data)
        if serializer.is_valid():
            audio_file = request.FILES.get('audio_file')
            if audio_file:
                # Проверяем формат файла
                allowed_formats = ['mp3', 'aac', 'wav', 'flac', 'dsd']
                file_extension = audio_file.name.split(
                    '.')[-1].lower() if '.' in audio_file.name else None
                if file_extension not in allowed_formats:
                    return Response({'error': f'Invalid audio file format. Allowed formats: {", ".join(allowed_formats)}.'},
                                    status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def audio_files_delete(request):
    AudioFiles.objects.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def video_files_list(request):
    if request.method == 'GET':
        video_files = VideoFiles.objects.all()
        video_data = []
        for video in video_files:
            video_path = video.video_file.path

            # Измерение пропускной способности
            start_time = time.time()
            with open(video_path, 'rb') as video_file:
                response = HttpResponse(video_file, content_type='video/mp4')

            end_time = time.time()

            # Вычисление времени передачи
            duration = end_time - start_time

            # Размер файла в мегабайтах
            size_in_mb = round(video.video_file.size / (1024 * 1024), 2)

            # Подсчет пропускной способности в Mbps
            file_size_in_bytes = os.path.getsize(video_path)
            bandwidth = (file_size_in_bytes * 8) / \
                (duration * 1000000)  # Переводим в Mbps

            # Обновление поля пропускной способности в объекте VideoFiles
            video.bandwidth = bandwidth
            bandwidth_in_mbps = round(bandwidth, 2)
            video.save()

            # Формирование данных для JsonResponse
            video_info = {
                'id': video.id,
                'title_video': video.title_video,
                'description': video.description,
                'file_path': video.file_path,
                'video_file': {
                    'url': video.video_file.url,
                    'name': str(video.video_file),  # Имя файла
                    'size': f"{size_in_mb} MB",  # Размер файла в мегабайтах
                    'format': video.format,
                    'bandwidth_video_file': f"{bandwidth_in_mbps} Mbps"
                }
            }
            video_data.append(video_info)

        return JsonResponse(video_data, safe=False)

    elif request.method == 'POST':
        serializer = VideoFilesSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            print(request.FILES)
            video_file = request.FILES.get('video_file')
            if not video_file:
                return Response({'error': 'Video file is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Проверка формата файла
            allowed_formats = ['mp4', 'mkv']
            file_extension = video_file.name.split(
                '.')[-1].lower() if '.' in video_file.name else None
            print(f'File extension: {file_extension}')
            print(f'Allowed formats: {allowed_formats}')
            if file_extension not in allowed_formats:
                print('Invalid format!')
                return Response({'error': f'Invalid video file format. Allowed formats: {", ".join(allowed_formats)}.'},
                                status=status.HTTP_400_BAD_REQUEST)

            content_id = request.data.get('content_id')
            # Проверяем, существует ли контент с переданным content_id
            try:
                content = Content.objects.get(pk=content_id)
            except Content.DoesNotExist:
                return Response({'error': 'Invalid content_id. Content does not exist.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Сохранение файла в модели Video
            serializer.save(video_file=video_file, content_id=content)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_video_file(request, video_id):
    video = get_object_or_404(VideoFiles, pk=video_id)

    if request.method == 'PUT':
        serializer = VideoFilesSerializer(video, data=request.data)
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
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def video_files_delete(request):
    VideoFiles.objects.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
