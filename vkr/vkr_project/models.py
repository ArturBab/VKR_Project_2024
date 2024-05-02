from django.db import models
import time
from django.http import HttpResponse
from django.utils import timezone
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
    telegram_id = models.CharField(max_length=255, blank=True, null=True)

    objects = CustomUserManager()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    group_educational = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.user.username} - {self.message}'
    

class NotificationReadByStudent(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    

class Content(models.Model):
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    content_file = models.FileField(upload_to='content_files/')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='contents')
    group_educational = models.CharField(max_length=20)

    def __str__(self):
        return self.title


class VideoFiles(models.Model):
    title_video = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='video_files/')
    content_id = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name='video_files')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='videos')
    group_educational = models.CharField(max_length=20)

    def __str__(self):
        return self.title_video


class AudioFiles(models.Model):
    name_audio = models.CharField(max_length=255)
    creator_audio = models.CharField(max_length=255)
    data_create = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    audio_file = models.FileField(upload_to='audio_files/')
    content_id = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name='audio_file')
    video_id = models.OneToOneField(
        VideoFiles, on_delete=models.CASCADE, related_name='audio_file')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='audios')
    group_educational = models.CharField(max_length=20)

    def __str__(self):
        return self.name_audio
