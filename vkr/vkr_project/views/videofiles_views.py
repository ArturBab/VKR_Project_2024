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
