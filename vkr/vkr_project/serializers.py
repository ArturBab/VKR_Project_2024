from rest_framework import serializers
from .models import *


class ContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Content
        fields = '__all__'


class AudioFilesSerializer(serializers.ModelSerializer):

    class Meta:
        model = AudioFiles
        fields = '__all__'
        depth = 2


class VideoFilesSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoFiles
        fields = '__all__'
        depth = 1
