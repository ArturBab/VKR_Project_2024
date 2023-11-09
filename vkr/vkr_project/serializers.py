from rest_framework import serializers
from .models import *
from os.path import basename

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

    video_file = serializers.SerializerMethodField()

    def get_video_file(self, obj):
        request = self.context.get('request')
        if request and obj.video_file:
            return {
                'name': basename(obj.video_file.name),
                'url': request.build_absolute_uri(obj.video_file.url)
            }
        return None
