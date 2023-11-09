from django.db import models


class Content(models.Model):
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    content_file = models.FileField(upload_to='content_files/')


class VideoFiles(models.Model):
    title_video = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='video_files/')
    content_id = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name='video_files')


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
