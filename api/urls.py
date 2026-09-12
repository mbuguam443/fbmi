from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.me_view, name='me'),
    path('portal/', views.portal_view, name='portal'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/password/', views.change_password_view, name='change_password'),
    path('groups/', views.groups_view, name='groups'),
    path('givings/', views.givings_view, name='givings'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('events/', views.events_view, name='events'),
    path('events/<int:event_id>/register/', views.event_register_view, name='event_register'),
    path('announcements/', views.announcements_view, name='announcements'),
    path('sermons/', views.sermons_view, name='sermons'),
    path('prayers/', views.prayers_view, name='prayers'),
]