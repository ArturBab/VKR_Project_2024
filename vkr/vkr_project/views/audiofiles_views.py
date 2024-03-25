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
