from django.db import models
import time
from django.http import HttpResponse
import os
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        if not username:
            raise ValueError('Username is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    role = models.CharField(max_length=20)
    group = models.CharField(max_length=20, blank=True, null=True)

    objects = CustomUserManager()


class Content(models.Model):
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    content_file = models.FileField(upload_to='content_files/')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='contents')

    def __str__(self):
        return self.title


class VideoFiles(models.Model):
    title_video = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='video_files/')
    # Определяет пропускную способность видеофайла
    bandwidth = models.FloatField(null=True, blank=True)
    content_id = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name='video_files')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='videos')

    def __str__(self):
        return self.title_video

    def update_bandwidth_video(self):
        try:
            video_path = self.video_file.path

            # Измеренеие пропускной способности
            start_time = time.time()
            with open(video_path, 'rb') as video_file:
                # Отправляем видеофайл клиенту (это может быть не обязательно для вашего случая)
                response = HttpResponse(video_file, content_type='video/mp4')

            end_time = time.time()

            # Вычисление времени передачи
            duration = end_time - start_time

            # Подсчет пропускной способности в Mbps
            file_size_in_bytes = os.path.getsize(video_path)
            bandwidth = (file_size_in_bytes * 8) / \
                (duration * 1000000)  # Переводим в Mbps

            # Обновление поля пропускной способности
            self.bandwidth = bandwidth
            self.save()

            return True  # Успешно обновлено
        except FileNotFoundError:
            return False  # Ошибка: файл не найден


class AudioFiles(models.Model):
    name_audio = models.CharField(max_length=255)
    creator_audio = models.CharField(max_length=255)
    data_create = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    audio_file = models.FileField(upload_to='audio_files/')
    # Определяет пропускную способность аудиофайла
    bandwidth = models.FloatField(null=True, blank=True)
    content_id = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name='audio_file')
    video_id = models.OneToOneField(
        VideoFiles, on_delete=models.CASCADE, related_name='audio_file')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='audios')

    def __str__(self):
        return self.name_audio

    def update_bandwidth_audio(self):
        try:
            audio_path = self.audio_file.path

            # Измеренеие пропускной способности
            start_time = time.time()
            with open(audio_path, 'rb') as audio_file:
                # Отправляем видеофайл клиенту (это может быть не обязательно для вашего случая)
                response = HttpResponse(audio_file, content_type='audio/mp3')

            end_time = time.time()

            # Вычисление времени передачи
            duration = end_time - start_time

            # Подсчет пропускной способности в Mbps
            file_size_in_bytes = os.path.getsize(audio_path)
            bandwidth = (file_size_in_bytes * 8) / \
                (duration * 1000000)  # Переводим в Mbps

            # Обновление поля пропускной способности
            self.bandwidth = bandwidth
            self.save()

            return True  # Успешно обновлено
        except FileNotFoundError:
            return False  # Ошибка: файл не найден
