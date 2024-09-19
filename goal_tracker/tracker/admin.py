from django.contrib import admin
from .models import Day, Category, Goal

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'all_goals_completed')
    list_filter = ('user', 'date')
    search_fields = ('user__username', 'date')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'user__username')

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'day', 'status', 'category', 'points', 'recurrent_until', 'until_date')
    list_filter = ('status', 'category', 'recurrent_until')
    search_fields = ('title', 'day__date', 'category__name')
    raw_id_fields = ('day', 'category')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('day', 'category')