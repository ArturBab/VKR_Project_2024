from django.contrib import admin
from django.urls import path
from vkr_project.views.content_views import content_list, update_content, content_delete
from vkr_project.views.audiofiles_views import audio_files_list, update_audio_file, audio_files_delete
from vkr_project.views.videofiles_views import video_files_list, update_video_file, video_files_delete
from django.conf import settings
from django.conf.urls.static import static
from vkr_project.views.user_views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from vkr_project.views.user_views import RegisterAPIView
from vkr_project.views_templates.templates_views import *


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/content/', content_list),
    path('api/content/update/<int:content_id>/',
         update_content, name='update_content'),
    path('api/content/delete/<int:content_id>/',
         content_delete, name='content-delete'),

    path('api/audio_files/', audio_files_list),
    path('api/audio/update/<int:audio_id>/',
         update_audio_file, name='update_audio_file'),
    path('api/audio/delete/', audio_files_delete, name='audio-files-delete'),

    path('api/video_files/', video_files_list),
    path('api/video/update/<int:video_id>/',
         update_video_file, name='update_video_file'),
    path('api/video/delete/<int:video_id>/',
         video_files_delete, name='video-files-delete'),

    path('api/register/', RegisterAPIView.as_view(), name='api-register'),
    path('api/login/', TokenObtainPairView.as_view(), name='login_with_token'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/students_list/', student_list, name='students_list'),
    path('api/groups_list/', list_student_groups, name='list_student_groups'),
    path('api/teachers_list/', teachers_list, name='teachers_list'),

    path('', home_view, name='home'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
