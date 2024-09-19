# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Day, Goal, Category
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.views.decorators.http import require_GET
from .forms import GoalForm
from django.db.models import Sum, Count, Case, When, IntegerField, F, Q
from django.utils import timezone
import logging
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods

User = get_user_model()

def custom_password_reset_view(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            associated_users = User.objects.filter(email=email)
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "registration/password_reset_email.html"
                    c = {
                        "email": user.email,
                        'domain': request.META['HTTP_HOST'],
                        'site_name': 'Your Site',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'https' if request.is_secure() else 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    send_mail(subject, email, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                return redirect("password_reset_done")
    else:
        form = PasswordResetForm()
    return render(request, "registration/password_reset_form.html", {"form": form})

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

@login_required
def calendar_view(request):
    today = datetime.today().date()
    current_day, created = Day.objects.get_or_create(user=request.user, date=today)
    
    # Ανάκτηση των στόχων για την τρέχουσα ημέρα
    goals = Goal.objects.filter(day=current_day)
    
    # Ανάκτηση των ημερών για τις τελευταίες 7 ημέρες
    past_week = [today - timedelta(days=i) for i in range(7)]
    days = Day.objects.filter(user=request.user, date__in=past_week).order_by('-date')
    
    context = {
        'current_day': current_day,
        'goals': goals,
        'days': days,
        'today': today,
    }
    return render(request, 'tracker/calendar.html', context)


from datetime import datetime

@login_required
def add_goal(request):
    try:
        data = json.loads(request.body)
        title = data.get('title')
        notes = data.get('notes')
        date_str = data.get('date')
        category_name = data.get('category')
        points = data.get('points')
        
        if not all([title, date_str]):
            return JsonResponse({'status': 'error', 'message': 'Missing title or date'}, status=400)
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        day, created = Day.objects.get_or_create(user=request.user, date=date)
        
        # Δημιουργία ή ανάκτηση της κατηγορίας
        category = None
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name, user=request.user)
        
        # Δημιουργία του στόχου
        goal = Goal.objects.create(
            day=day,
            title=title,
            notes=notes,
            category=category,
            points=points
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Goal added successfully',
            'goal': {
                'id': goal.id,
                'title': goal.title,
                'notes': goal.notes,
                'category': category_name if category else None,
                'points': goal.points
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def get_categories(request):
    query = request.GET.get('q', '')
    categories = Category.objects.filter(user=request.user, name__icontains=query)[:10]
    return JsonResponse({'categories': [{'id': c.id, 'name': c.name} for c in categories]})

@login_required
def update_goal_status(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, day__user=request.user)
    if request.method == 'POST':
        status = request.POST.get('status')
        goal.status = status
        goal.save()
        # Check if all goals are achieved
        if goal.day.all_goals_completed():
            request.session['celebrate'] = True
        return redirect('calendar')


@login_required
def add_notes(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, day__user=request.user)
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        goal.notes = notes
        goal.save()
        return redirect('calendar')
    return render(request, 'tracker/add_notes.html', {'goal': goal})


@login_required
def get_goal(request, goal_id):
    try:
        goal = Goal.objects.get(id=goal_id, day__user=request.user)
        return JsonResponse({
            'id': goal.id,
            'title': goal.title,
            'notes': goal.notes,
            'status': goal.status,
            'category': goal.category.name if goal.category else None,
            'points': goal.points
        })
    except Goal.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Goal not found'}, status=404)

@login_required
@require_POST
def update_goals(request):
    data = json.loads(request.body)
    goals = data.get('goals', [])
    for goal_data in goals:
        try:
            goal = Goal.objects.get(id=goal_data['id'], day__user=request.user)
            goal.status = 'completed' if goal_data['completed'] else 'pending'
            goal.save()
        except Goal.DoesNotExist:
            pass
    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def delete_goal(request, goal_id):
    try:
        goal = Goal.objects.get(id=goal_id, day__user=request.user)
        goal.delete()
        return JsonResponse({'status': 'success'})
    except Goal.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Goal not found'}, status=404)

@login_required
@require_GET
def get_goals(request, date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        day, created = Day.objects.get_or_create(user=request.user, date=date_obj)
        goals = Goal.objects.filter(day=day)
        
        total_points = sum(goal.points for goal in goals if goal.points is not None)
        completed_points = sum(goal.points for goal in goals if goal.status == 'completed' and goal.points is not None)
        
        completion_percentage = (completed_points / total_points * 100) if total_points > 0 else 0
        
        goals_data = [{
            'id': goal.id,
            'title': goal.title,
            'status': goal.status,
            'category': goal.category.name if goal.category else None,
            'points': goal.points if goal.points is not None else 0
        } for goal in goals]
        
        return JsonResponse({
            'status': 'success', 
            'goals': goals_data,
            'completion_percentage': round(completion_percentage, 2)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

logger = logging.getLogger(__name__)

@login_required
def get_user_statistics(request):
    try:
        user = request.user
        all_user_days = Day.objects.filter(user=user)
        all_user_goals = Goal.objects.filter(day__user=user)
        
        if not all_user_goals.exists():
            return JsonResponse({
                'perfect_days': "0/0",
                'overall_completion_rate': 0,
                'last_30_days_completion_rate': 0,
                'all_users_completion_rate': 0
            })
        
        # Υπολογισμός τέλειων ημερών
        days_with_goals = all_user_days.annotate(goals_count=Count('goals')).filter(goals_count__gt=0)
        total_days_with_goals = days_with_goals.count()
        
        perfect_days = days_with_goals.annotate(
            completed_goals=Count('goals', filter=Q(goals__status='completed')),
            total_goals=Count('goals')
        ).filter(completed_goals=F('total_goals')).count()
        
        # Υπολογισμός συνολικού ποσοστού ολοκλήρωσης
        total_points = all_user_goals.aggregate(Sum('points'))['points__sum'] or 0
        completed_points = all_user_goals.filter(status='completed').aggregate(Sum('points'))['points__sum'] or 0
        overall_completion_rate = (completed_points / total_points * 100) if total_points > 0 else 0
        
        # Υπολογισμός ποσοστού ολοκλήρωσης τελευταίων 30 ημερών
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        last_30_days_goals = all_user_goals.filter(day__date__gte=thirty_days_ago)
        last_30_days_points = last_30_days_goals.aggregate(Sum('points'))['points__sum'] or 0
        last_30_days_completed_points = last_30_days_goals.filter(status='completed').aggregate(Sum('points'))['points__sum'] or 0
        last_30_days_completion_rate = (last_30_days_completed_points / last_30_days_points * 100) if last_30_days_points > 0 else 0
        
        # Υπολογισμός μέσου όρου όλων των χρηστών
        all_users_completion_rate = Goal.objects.aggregate(
            total_points=Sum('points'),
            completed_points=Sum(Case(When(status='completed', then='points'), default=0, output_field=IntegerField()))
        )
        all_users_rate = (all_users_completion_rate['completed_points'] / all_users_completion_rate['total_points'] * 100) if all_users_completion_rate['total_points'] > 0 else 0
        
        return JsonResponse({
            'perfect_days': f"{perfect_days}/{total_days_with_goals}",
            'overall_completion_rate': round(overall_completion_rate, 2),
            'last_30_days_completion_rate': round(last_30_days_completion_rate, 2),
            'all_users_completion_rate': round(all_users_rate, 2)
        })
    except Exception as e:
        logger.error(f"Error in get_user_statistics: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    

@login_required
def update_goal(request, goal_id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        title = data.get('title')
        notes = data.get('notes')
        date_str = data.get('date')
        category_name = data.get('category')
        points = data.get('points')
        
        if title and date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            goal = Goal.objects.get(id=goal_id, day__user=request.user)
            goal.title = title
            goal.notes = notes
            
            if goal.day.date != date:
                new_day, created = Day.objects.get_or_create(user=request.user, date=date)
                goal.day = new_day
            
            if category_name:
                category, _ = Category.objects.get_or_create(name=category_name, user=request.user)
                goal.category = category
            else:
                goal.category = None
            
            if points is not None:
                goal.points = points
            
            goal.save()
            return JsonResponse({'status': 'success', 'message': 'Goal updated successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def profile_view(request):
    return render(request, 'profile.html')

@login_required
@require_http_methods(["POST"])
def make_goal_recurrent(request, goal_id):
    data = json.loads(request.body)
    recurrent_until = data.get('recurrent_until')
    until_date = data.get('until_date')

    try:
        goal = Goal.objects.get(id=goal_id, day__user=request.user)
        
        if recurrent_until == 'date':
            until_date = timezone.datetime.strptime(until_date, "%Y-%m-%d").date()
            max_date = timezone.now().date() + timedelta(days=365)
            if until_date > max_date:
                return JsonResponse({'status': 'error', 'message': 'Date cannot exceed one year from now'})
        elif recurrent_until == 'year':
            until_date = timezone.now().date() + timedelta(days=365)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid recurrent option'})

        goal.recurrent_until = recurrent_until
        goal.until_date = until_date
        goal.save()
        goal.create_recurrent_goals()
        return JsonResponse({'status': 'success'})
    except Goal.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Goal not found'})

@login_required
@require_http_methods(["POST"])
def stop_recurrent_goal(request, goal_id):
    try:
        goal = Goal.objects.get(id=goal_id, day__user=request.user)
        goal.stop_recurrent_goal()
        return JsonResponse({'status': 'success', 'message': 'Recurrent goal stopped and future occurrences deleted'})
    except Goal.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Goal not found'})