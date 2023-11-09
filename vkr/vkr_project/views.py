from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import mimetypes
from rest_framework.parsers import FileUploadParser
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest

from .models import *
from .serializers import *


@api_view(['GET', 'POST'])
def content_list(request):
    if request.method == 'GET':
        content = Content.objects.all()
        serializer = ContentSerializer(content, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ContentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            content_file = request.FILES.get('content_file')
            if content_file:
                ###
                # Сохранение файла в модели Content
                content = serializer.instance
                content.content_file = content_file
                content.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
def content_delete(request):
    Content.objects.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def audio_files_list(request):
    if request.method == 'GET':
        audio_files = AudioFiles.objects.all()
        serializer = AudioFilesSerializer(audio_files, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = AudioFilesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            audio_file = request.FILES.get('audio_file')
            if audio_file:

                # Проверка формата файла
                file_format, _ = mimetypes.guess_type(audio_file.name)
                if not file_format or not file_format.startswith('audio'):
                    return Response({'error': 'Invalid audio file format.'}, status=status.HTTP_400_BAD_REQUEST)

                # Сохранение файла в модели Audio
                audio = serializer.instance
                audio.audio_file = audio_file
                audio.save()

                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response({'error': 'Audio file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def audio_files_delete(request):
    AudioFiles.objects.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def video_files_list(request):
    if request.method == 'GET':
        video_files = VideoFiles.objects.all()
        serializer = VideoFilesSerializer(
            video_files, many=True, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VideoFilesSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            print(request.FILES)
            video_file = request.FILES.get('video_file')
            if not video_file:
                return Response({'error': 'Video file is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Проверка формата файла
            allowed_formats = ['mp4', 'mkv', 'wav']
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
                return Response({'error': 'Invalid content_id. Content does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

            # Сохранение файла в модели Video
            serializer.save(video_file=video_file, content_id=content)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def video_files_delete(request):
    VideoFiles.objects.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
