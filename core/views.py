from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import models
from skill_sessions.models import SkillSwapRequest, SkillSwapSession

def home(request):
    return render(request, "core/home.html")

class HomeView:
    @classmethod
    def as_view(cls):
        return home

class DashboardView:
    @classmethod
    def as_view(cls):
        return lambda r: render(r, "core/dashboard.html")

class RequestsView:
    @classmethod
    def as_view(cls):
        @login_required
        def requests_view(request):
            # Get received requests for the current user
            received_requests = SkillSwapRequest.objects.filter(
                recipient=request.user
            ).select_related(
                'requester', 'offered_skill__skill'
            ).order_by('-created_at')
            
            # Get sent requests by the current user
            sent_requests = SkillSwapRequest.objects.filter(
                requester=request.user
            ).select_related(
                'recipient', 'offered_skill__skill'
            ).order_by('-created_at')
            
            # Get active sessions for the current user
            active_sessions = SkillSwapSession.objects.filter(
                models.Q(teacher=request.user) | models.Q(learner=request.user),
                status__in=['scheduled', 'in_progress']
            ).select_related(
                'teacher', 'learner', 'skill'
            ).order_by('scheduled_date')
            
            # Calculate stats
            stats = {
                'total_requests': received_requests.count() + sent_requests.count(),
                'pending_requests': received_requests.filter(status='pending').count() + sent_requests.filter(status='pending').count(),
                'accepted_requests': received_requests.filter(status='accepted').count() + sent_requests.filter(status='accepted').count(),
                'active_sessions': active_sessions.count(),
            }
            
            context = {
                'received_requests': received_requests,
                'sent_requests': sent_requests,
                'active_sessions': active_sessions,
                'stats': stats,
            }
            
            return render(request, "core/requests.html", context)
            
        return requests_view

class UserProfileView:
    @classmethod
    def as_view(cls):
        return lambda r, user_id: render(r, "core/user_profile.html")

class SearchView:
    @classmethod
    def as_view(cls):
        return lambda r: render(r, "core/search.html")

class NotificationListView:
    @classmethod
    def as_view(cls):
        return lambda r: render(r, "core/notifications.html")

def mark_notification_read(request, notification_id):
    return JsonResponse({"status": "success"})

def mark_all_notifications_read(request):
    return JsonResponse({"status": "success"})
