"""
APP URL
"""

from django.urls import path
from . import views
from chat.views import my_404, error_500
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("", views.home, name='home'),
    path("login/", views.user_login, name="user_login"),
    path("signup/", views.signup, name='signup'),
]

urlpatterns += staticfiles_urlpatterns()

handler404 = my_404
handler500 = error_500
