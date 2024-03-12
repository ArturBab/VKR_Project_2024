from django.contrib import admin
from django.urls import path
from vkr_project import views
from django.conf import settings
from django.conf.urls.static import static
from vkr_project.user_views import register_view, login_view, user_view, logout_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


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

     path('api/register/', register_view, name='registration'),
     path('api/login/', login_view, name='login'),
     path('api/auth_user/', user_view, name='auth'),
     path('api/logout/', logout_view, name='logout'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
