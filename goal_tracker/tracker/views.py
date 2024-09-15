# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Day, Goal
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.views.decorators.http import require_GET

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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            notes = data.get('notes')
            date_str = data.get('date')
            
            if not all([title, date_str]):
                return JsonResponse({'status': 'error', 'message': 'Missing title or date'}, status=400)
            
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            day, created = Day.objects.get_or_create(user=request.user, date=date)
            goal = Goal.objects.create(day=day, title=title, notes=notes)
            return JsonResponse({'status': 'success', 'message': 'Goal added successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def update_goal(request, goal_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title')
        notes = data.get('notes')
        date_str = data.get('date')
        
        if title and date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            goal = Goal.objects.get(id=goal_id, day__user=request.user)
            goal.title = title
            goal.notes = notes
            
            if goal.day.date != date:
                new_day, created = Day.objects.get_or_create(user=request.user, date=date)
                goal.day = new_day
            
            goal.save()
            return JsonResponse({'status': 'success', 'message': 'Goal updated successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


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
            'status': goal.status
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
        goals_data = [{'id': goal.id, 'title': goal.title, 'status': goal.status} for goal in goals]
        return JsonResponse({'status': 'success', 'goals': goals_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)