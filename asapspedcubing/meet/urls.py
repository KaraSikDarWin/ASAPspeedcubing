from django.contrib import admin
from django.urls import path, include
from . import views
from contest.views import submit_result, ResultContestUpdateView, ResultContestDeleteView


app_name = "meet"

urlpatterns = [
    path('', views.index, name='index'),
    path('meet/<int:pk>/edit/', views.add_meet, name='edit_meet'),
    path('meet/<int:pk>/delete/', views.delete_meet, name='delete_meet'),
    path('meet/<int:pk>/results/', views.edit_results, name='edit_results'),
    path('meet/<int:pk>/submit-result/', submit_result, name='submitresult'),
    path('meet/<int:pk>/', views.meet_detail, name='meet_detail'),
    path('meet/add/', views.add_meet, name='add_meet'),
    path('meet/<int:pk>/files/', views.manage_meet_files, name='manage_meet_files'),
    path('meet/<int:meet_pk>/files/delete/<int:file_pk>/', views.delete_meet_file, name='delete_meet_file'),

    path('disciplines/', views.DisciplinesListView.as_view(), name='disciplines_list'),
    path('disciplines/create/', views.DisciplinesCreateView.as_view(), name='disciplines_create'),
    path('disciplines/<int:pk>/edit/', views.DisciplinesUpdateView.as_view(), name='disciplines_update'),
    path('disciplines/<int:pk>/delete/', views.DisciplinesDeleteView.as_view(), name='disciplines_delete'), 

    path('competitors/', views.CompetitorListView.as_view(), name='competitors_list'),
    path('competitors/create/', views.CompetitorCreateView.as_view(), name='competitors_create'),
    path('competitors/<int:pk>/edit/', views.CompetitorUpdateView.as_view(), name='competitors_update'),
    path('competitors/<int:pk>/delete/', views.CompetitorDeleteView.as_view(), name='competitors_delete'),

    path('contest-result/<int:pk>/edit/', ResultContestUpdateView.as_view(), name='contest-result-update'),
    path('contest-result/<int:pk>/delete/', ResultContestDeleteView.as_view(), name='contest-result-delete'),
    

    path('api/v1/get-results/', views.GetResultsAPIView.as_view(), name='api_get_results'),
    path('api/v1/delete-results/', views.DeleteResultsAPIView.as_view(), name='api_delete_results'),
    path('api/v1/change-result-status/', views.change_result_status, name='change_result_status'),
    

]
