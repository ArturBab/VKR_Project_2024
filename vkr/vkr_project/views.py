from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def audio_files_delete(request):
    AudioFiles.objects.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def video_files_list(request):
    if request.method == 'GET':
        video_files = VideoFiles.objects.all()
        serializer = VideoFilesSerializer(video_files, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VideoFilesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def video_files_delete(request):
    VideoFiles.objects.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
