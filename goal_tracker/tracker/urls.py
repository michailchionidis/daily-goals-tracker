from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('add_goal/', views.add_goal, name='add_goal'),
    path('update_goal_status/<int:goal_id>/', views.update_goal_status, name='update_goal_status'),
    path('add_notes/<int:goal_id>/', views.add_notes, name='add_notes'),
    path('get_goal/<int:goal_id>/', views.get_goal, name='get_goal'),
    path('update_goal/<int:goal_id>/', views.update_goal, name='update_goal'),
    path('update_goals/', views.update_goals, name='update_goals'),
    path('delete_goal/<int:goal_id>/', views.delete_goal, name='delete_goal'),
    path('get_goals/<str:date>/', views.get_goals, name='get_goals'),
]
