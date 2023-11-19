from django.contrib import admin
from django.urls import path
from vkr_project import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/content/', views.content_list),
    path('api/content/update/<int:content_id>/',
         views.update_content, name='update_content'),
    path('api/content/delete/<int:audio_id>/',
         views.content_delete, name='content-delete'),

    path('api/audio_files/', views.audio_files_list),
    path('api/audio/update/<int:audio_id>/',
         views.update_audio_file, name='update_audio_file'),
    path('api/audio/delete/', views.audio_files_delete, name='audio-files-delete'),

    path('api/video_files/', views.video_files_list),
    path('api/video/update/<int:video_id>/',
         views.update_video_file, name='update_video_file'),
    path('api/video/delete/<int:video_id>/',
         views.video_files_delete, name='video-files-delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
