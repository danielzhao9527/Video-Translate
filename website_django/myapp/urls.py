from django.urls import path
from .views import get_video_info, generate_subtitles
from . import views
urlpatterns = [
    # path('video/<str:filename>/', views.stream_video, name='stream_video'),
    path('get_video_info/', get_video_info, name='get_video_info'),  # 获取视频信息
    path('generate_subtitles/', generate_subtitles, name='generate_subtitles'),  # 获取并翻译字幕
]
