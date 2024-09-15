from django import forms
from .models import Goal, Category
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
    
class GoalForm(forms.ModelForm):
    category = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = Goal
        fields = ['title', 'notes', 'category', 'points']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(GoalForm, self).__init__(*args, **kwargs)
        self.fields['points'].widget = forms.NumberInput(attrs={'min': 0, 'max': 10})

    def clean_category(self):
        category_name = self.cleaned_data.get('category')
        if category_name:
            category, created = Category.objects.get_or_create(name=category_name, user=self.user)
            return category
        return None