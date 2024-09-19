from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.profile_view, name='profile'),

    path('add_goal/', views.add_goal, name='add_goal'),
    path('update_goal_status/<int:goal_id>/', views.update_goal_status, name='update_goal_status'),
    path('add_notes/<int:goal_id>/', views.add_notes, name='add_notes'),
    path('get_goal/<int:goal_id>/', views.get_goal, name='get_goal'),
    path('update_goal/<int:goal_id>/', views.update_goal, name='update_goal'),
    path('update_goals/', views.update_goals, name='update_goals'),
    path('delete_goal/<int:goal_id>/', views.delete_goal, name='delete_goal'),
    path('get_goals/<str:date>/', views.get_goals, name='get_goals'),
    path('get_categories/', views.get_categories, name='get_categories'),
    path('get_user_statistics/', views.get_user_statistics, name='get_user_statistics'),
    path('make_goal_recurrent/<int:goal_id>/', views.make_goal_recurrent, name='make_goal_recurrent'),
]

