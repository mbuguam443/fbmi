from django.urls import path
from . import views

app_name = 'songs'

urlpatterns = [
    path('', views.SongListView.as_view(), name='song_list'),
    path('<int:pk>/', views.SongDetailView.as_view(), name='song_detail'),
]
