from django.db import models
import time
from django.http import HttpResponse
import os
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)
    

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    roles = models.ManyToManyField('Role', related_name='custom_users', blank=True)
    objects = CustomUserManager()

    def __str__(self):
        return self.username    


class Role(models.Model):
    role = models.CharField(max_length=255)
    is_root = models.BooleanField(default=False)

    def __str__(self):
        return self.role
    

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    first_name = models.CharField(max_length=20)
    middle_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Student(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='student_profile')
    stud_id = models.CharField(max_length=10)
    stud_group = models.CharField(max_length=15)
    course = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.stud_id} {self.stud_group}"
    

class Teacher(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='teacher_profile')
    teach_id = models.CharField(max_length=10)
    discipline = models.CharField(max_length=50)

    def __str__(self):
        return self.teach_id, self.discipline    


class Content(models.Model):
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    content_file = models.FileField(upload_to='content_files/')
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='contents')

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
        UserProfile, on_delete=models.CASCADE, related_name='videos')

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
        UserProfile, on_delete=models.CASCADE, related_name='audios')

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
