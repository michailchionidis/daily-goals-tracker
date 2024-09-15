# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from datetime import date

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
    day = models.ForeignKey(Day, related_name='goals', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Pending')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    points = models.IntegerField(default=0)

    def __str__(self):
        return self.title
