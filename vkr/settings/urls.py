from django.contrib import admin
from django.urls import path, include, re_path
from vkr_project.views.content_views import content_list, update_content, content_delete, telegram_content_detail
from vkr_project.views.audiofiles_views import audio_files_list, update_audio_file, audio_files_delete
from vkr_project.views.videofiles_views import video_files_list, update_video_file, video_files_delete, send_video_to_telegram_view
from vkr_project.views.notifications_views import (create_notification, 
                                                   mark_group_notifications_as_read, 
                                                   group_notification_status)

from vkr_project.telegram import *
from django.conf import settings
from django.conf.urls.static import static
from vkr_project.views.user_views import *
from vkr_project.views_templates.templates_views import *


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/content/', content_list, name='api-content_list'),

    path('telegram/content/<int:content_id>/', telegram_content_detail, name='telegram_content_detail'),

    path('api/content/update/<int:content_id>/',
         update_content, name='update_content'),
    path('api/content/delete/<int:content_id>/',
         content_delete, name='content-delete'),

    path('api/audio_files/', audio_files_list),
    path('api/audio/update/<int:audio_id>/',
         update_audio_file, name='update_audio_file'),
    path('api/audio/delete/', audio_files_delete, name='audio-files-delete'),

    path('api/video_files/', video_files_list),

    path('telegram/send_video/<int:video_id>/', send_video_to_telegram_view, name='send_video_to_telegram'),

    path('api/video/update/<int:video_id>/',
         update_video_file, name='update_video_file'),
    path('api/video/delete/<int:video_id>/',
         video_files_delete, name='video-files-delete'),

     path('api/notification-create/', create_notification, name='api-notification-create'),
     path('api/notification-read/', mark_group_notifications_as_read, name='api-notification-read'),
     path('api/notification-status/', group_notification_status, name='api-notification-status'),

     #path('api/create_group_chat/', create_group_chat, name='create_group_chat'),
     #path('api/start_command-telegram/', start_command_telegram, name='start_command'),
     path('api/send-notification-telegram/', send_telegram_notification, name='send_notification'),


    path('api/register/', RegisterAPIView.as_view(), name='api-register'),
    path('api/auth/', include('djoser.urls'), name='api-auth'),
    re_path(r'^auth/', include('djoser.urls.authtoken')),

    path('api/students_list/', student_list, name='students_list'),
    path('api/groups_list/', list_student_groups_API, name='api_list_student_groups'),
    path('api/students_list/<str:group>/', StudentAPIListView.as_view(), name='api_students_list'),
    path('api/teachers_list/', teachers_list, name='teachers_list'),

    path('', home_view, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
    #path('logout/', logout_view, name='logout'),
    path('teacher_page/', teacher_page_view, name='teacher_page'),
    path('student_groups/', student_groups_view, name='student_groups_view'),
    path('students_list/<str:group>/', students_list, name='students_list'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
