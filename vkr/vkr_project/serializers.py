from rest_framework import serializers
from .models import *
from os.path import basename


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'middle_name',
                  'last_name', 'email', 'password', 'role', 'group']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        role = validated_data.get('role')
        group = validated_data.get('group')

        if role == 'Teacher':
            validated_data.pop('group', None)
        elif role == 'Student':
            if not group:
                raise serializers.ValidationError(
                    "Для студента необходимо указать группу.")
        else:
            raise serializers.ValidationError("Недопустимая роль.")

        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)

        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance


class AudioFilesSerializer(serializers.ModelSerializer):

    class Meta:
        model = AudioFiles
        fields = '__all__'
        depth = 1

    audio_file = serializers.SerializerMethodField()

    def get_audio_file(self, obj):
        request = self.context.get('request')
        if request and obj.audio_file:
            return {
                'name': basename(obj.audio_file.name),
                'url': request.build_absolute_uri(obj.audio_file.url)
            }
        return None
    
    def create(self, validated_data):
        # Добавляем поле group_educational из запроса
        group_educational = validated_data.pop('group_educational', None)

        # Создаем новый объект контента с указанием группы
        audioofiles = VideoFiles.objects.create(group_educational=group_educational, **validated_data)
        return audioofiles


class ContentSerializer(serializers.ModelSerializer):

    audio_files = AudioFilesSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False, 'allow_null': True}  # Делаем поле user необязательным
        }

    def create(self, validated_data):
        # Добавляем поле group_educational из запроса
        group_educational = validated_data.pop('group_educational', None)

        # Создаем новый объект контента с указанием группы
        content = Content.objects.create(group_educational=group_educational, **validated_data)
        return content
    
    def get_video_files(self, obj):
        video_files = obj.video_files.all()
        serializer = VideoFilesSerializer(video_files, many=True)
        return serializer.data
    
    

class VideoFilesSerializer(serializers.ModelSerializer):
    content = ContentSerializer(read_only=True)
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
    
    def create(self, validated_data):
        # Добавляем поле group_educational из запроса
        group_educational = validated_data.pop('group_educational', None)

        # Создаем новый объект контента с указанием группы
        videofiles = VideoFiles.objects.create(group_educational=group_educational, **validated_data)
        return videofiles
