from django.urls import path
from . import views

app_name = 'giving'

urlpatterns = [
    path('', views.GivingListView.as_view(), name='giving-list'),
    path('create/', views.GivingCreateView.as_view(), name='giving-create'),
    path('basket/', views.giving_record_basket, name='giving-basket'),
    path('<int:pk>/update/', views.GivingUpdateView.as_view(), name='giving-update'),
    path('<int:pk>/delete/', views.GivingDeleteView.as_view(), name='giving-delete'),
    path('<int:pk>/refresh-mpesa/', views.giving_refresh_mpesa_status, name='giving-refresh-mpesa'),
]
