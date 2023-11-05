from django.contrib import admin
from .models import Content, AudioFiles, VideoFiles

admin.site.register(Content)
admin.site.register(AudioFiles)
admin.site.register(VideoFiles)
# Register your models here.
