from django.urls import path
from . import views

app_name = 'bible_study'

urlpatterns = [
    path('', views.BibleStudyListView.as_view(), name='study_list'),
    path('<int:pk>/', views.BibleStudyDetailView.as_view(), name='study_detail'),
]
