from django.contrib import admin
from django.urls import path
from vkr_project import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/content/', views.content_list),
    path('content/delete/', views.content_delete, name='content-delete'),
    path('api/audio_files/', views.audio_files_list),
    path('audio/delete/', views.audio_files_delete, name='audio-files-delete'),
    path('api/video_files/', views.video_files_list),
    path('video/delete/', views.video_files_delete, name='video-files-delete'),
    path('measure-bandwidth_video/<int:video_id>/',
         views.measure_bandwidth_video, name='measure_bandwidth_video'),
    path('measure-bandwidth_audio/<int:audio_id>/',
         views.measure_bandwidth_audio, name='measure_bandwidth_audio'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
