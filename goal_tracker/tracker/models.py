# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.utils import timezone
from datetime import timedelta


class Day(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return self.date.strftime("%Y-%m-%d")

    def all_goals_completed(self):
        return self.goals.filter(status='Pending').count() == 0 and self.goals.exists()
    
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Goal(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Achieved', 'Achieved'),
        ('Failed', 'Failed'),
    ]
    RECURRENT_CHOICES = [
        ('date', 'Until Date'),
        ('year', 'For One Year'),
    ]
    day = models.ForeignKey(Day, related_name='goals', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Pending')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    points = models.IntegerField(default=0)
    recurrent_until = models.CharField(max_length=10, choices=RECURRENT_CHOICES, blank=True, null=True)
    until_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title

    def create_recurrent_goals(self):
        if self.recurrent_until:
            current_date = timezone.now().date()
            if self.recurrent_until == 'date':
                end_date = min(self.until_date, current_date + timedelta(days=365))
            else:  # 'year'
                end_date = current_date + timedelta(days=365)
            
            next_date = self.day.date + timedelta(days=1)
            while next_date <= end_date:
                day, created = Day.objects.get_or_create(user=self.day.user, date=next_date)
                Goal.objects.create(
                    day=day,
                    title=self.title,
                    notes=self.notes,
                    status='Pending',
                    category=self.category,
                    points=self.points,
                    recurrent_until=self.recurrent_until,
                    until_date=self.until_date
                )
                next_date += timedelta(days=1)

    def stop_recurrent_goal(self):
        if self.recurrent_until:
            current_date = timezone.now().date()
            Goal.objects.filter(
                title=self.title,
                day__date__gt=current_date,
                recurrent_until=self.recurrent_until,
                until_date=self.until_date
            ).delete()
            self.recurrent_until = None
            self.until_date = None
            self.save()