from django.urls import path, include
from . import views

urlpatterns = [
    path('<int:pk>/', views.contest_detail, name='detail'),
]
