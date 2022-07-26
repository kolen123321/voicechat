from . import views
from django.urls import path

urlpatterns = [
    path('', views.VoiceView.as_view()),
]
