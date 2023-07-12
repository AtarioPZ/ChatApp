"""
APP URL
"""

from django.urls import path
from . import views
from .views import my_404, error_500
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("", views.home, name='home'),
    path("accounts/login/", views.user_login, name="user_login"),
    path("signup/", views.signup, name='signup'),
    path("profile/", views.profile, name='profile'),
    path('logout/', views.logout, name='logout'),
    path('reset-session/', views.reset_session, name='reset_session'),
    path('chat/', views.chatpage, name='chatpage'),
    path('chat/<str:username>/', views.chatpage, name='chatpage_with_username'),
    
]

urlpatterns += staticfiles_urlpatterns()

handler404 = my_404
handler500 = error_500
