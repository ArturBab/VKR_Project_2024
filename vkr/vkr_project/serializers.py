from rest_framework import serializers
from .models import *
from os.path import basename
import re
import pytz
from django.utils.dateformat import DateFormat
from django.utils.formats import time_format


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'middle_name',
                  'last_name', 'email', 'password', 'role', 'group', 'telegram_id']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_telegram_id(self, value):
        """
        Проверка: telegram_id указан для студента и соответствует шаблону ссылки на телеграмм.
        """
        role = self.initial_data.get('role')  # Получаем роль из входных данных
        if role == 'Student':
            if not value:
                raise serializers.ValidationError(
                    "Для студента необходимо указать telegram_id.")
            # Проверяем, соответствует ли значение шаблону ссылки на телеграмм
            if not re.match(r'^(?:@|\bhttps://t\.me/)\w+$', value) and not re.match(r'^https://t.me/\w+$', value):
                raise serializers.ValidationError(
                    "Некорректная ссылка на телеграмм.")
        return value

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


class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    created_at = serializers.SerializerMethodField()
    read_by_students = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'created_at', 'is_read', 'group_educational', 'read_by_students']
        read_only_fields = ['id', 'created_at', 'is_read']

    def get_created_at(self, obj):
        moscow_timezone = pytz.timezone('Europe/Moscow')
        moscow_time = timezone.localtime(timezone.now(), moscow_timezone)
        formatted_time = moscow_time.strftime('%d-%m-%Y, %H:%M')
        return formatted_time

    def get_read_by_students(self, obj):
        read_by_students = NotificationReadByStudent.objects.filter(notification=obj)
        return [
            {
                'student': read_by_student.student.username,
                'read_status': 'Read' if read_by_student.is_read else 'Not Read'
            }
            for read_by_student in read_by_students
        ]

    def create(self, validated_data):
        message = validated_data.get('message')
        group_educational = validated_data.get('group_educational')
        user = validated_data.get('user')  # Получаем пользователя, отправившего уведомление
        instance = Notification.objects.create(user=user, message=message, group_educational=group_educational)
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
        audioofiles = VideoFiles.objects.create(
            group_educational=group_educational, **validated_data)
        return audioofiles


class ContentSerializer(serializers.ModelSerializer):

    audio_files = AudioFilesSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        fields = '__all__'
        extra_kwargs = {
            # Делаем поле user необязательным
            'user': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        # Добавляем поле group_educational из запроса
        group_educational = validated_data.pop('group_educational', None)

        # Создаем новый объект контента с указанием группы
        content = Content.objects.create(
            group_educational=group_educational, **validated_data)
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
        videofiles = VideoFiles.objects.create(
            group_educational=group_educational, **validated_data)
        return videofiles
