from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import models

from .models import SkillSwapRequest, SkillSwapSession, SessionReview
from .forms import SkillSwapRequestForm, RequestResponseForm, SessionScheduleForm, SessionReviewForm
from skills.models import OfferedSkill, DesiredSkill

# Create your views here.

class RequestListView(LoginRequiredMixin, ListView):
    model = SkillSwapRequest
    template_name = 'skill_sessions/request_list.html'
    context_object_name = 'requests'
    
    def get_queryset(self):
        return SkillSwapRequest.objects.filter(
            requester=self.request.user
        ).select_related('recipient', 'offered_skill')


class SentRequestListView(LoginRequiredMixin, ListView):
    model = SkillSwapRequest
    template_name = 'skill_sessions/sent_requests.html'
    context_object_name = 'requests'
    
    def get_queryset(self):
        return SkillSwapRequest.objects.filter(
            requester=self.request.user
        ).select_related('recipient', 'offered_skill')


class ReceivedRequestListView(LoginRequiredMixin, ListView):
    model = SkillSwapRequest
    template_name = 'skill_sessions/received_requests.html'
    context_object_name = 'requests'
    
    def get_queryset(self):
        return SkillSwapRequest.objects.filter(
            recipient=self.request.user
        ).select_related('requester', 'offered_skill')


class SendRequestView(LoginRequiredMixin, CreateView):
    model = SkillSwapRequest
    form_class = SkillSwapRequestForm
    template_name = 'skill_sessions/send_request.html'
    success_url = reverse_lazy('skill_sessions:request_list')
    
    def form_valid(self, form):
        form.instance.requester = self.request.user
        form.instance.recipient_id = self.kwargs['user_id']
        return super().form_valid(form)


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = SkillSwapRequest
    template_name = 'skill_sessions/request_detail.html'
    context_object_name = 'request'
    
    def get_queryset(self):
        return SkillSwapRequest.objects.filter(
            requester=self.request.user
        ) | SkillSwapRequest.objects.filter(
            recipient=self.request.user
        )


class RequestResponseView(LoginRequiredMixin, UpdateView):
    model = SkillSwapRequest
    form_class = RequestResponseForm
    template_name = 'skill_sessions/request_response.html'
    success_url = reverse_lazy('skill_sessions:session_list')
    
    def get_queryset(self):
        return SkillSwapRequest.objects.filter(recipient=self.request.user)
    
    def post(self, request, *args, **kwargs):
        # Handle simple approve/decline actions
        if 'action' in request.POST:
            request_obj = self.get_object()
            action = request.POST.get('action')
            
            if action == 'accept':
                request_obj.status = 'accepted'
                request_obj.responded_at = timezone.now()
                request_obj.save()
                messages.success(request, f'Session request from {request_obj.requester.username} has been approved!')
            elif action == 'decline':
                request_obj.status = 'declined'
                request_obj.responded_at = timezone.now()
                request_obj.save()
                messages.success(request, f'Session request from {request_obj.requester.username} has been declined.')
            
            return redirect(self.success_url)
        
        return super().post(request, *args, **kwargs)


@login_required
def cancel_request(request, pk):
    request_obj = get_object_or_404(SkillSwapRequest, pk=pk, requester=request.user)
    request_obj.status = 'cancelled'
    request_obj.save()
    return redirect('skill_sessions:request_list')


class SessionListView(LoginRequiredMixin, ListView):
    model = SkillSwapSession
    template_name = 'skill_sessions/session_list.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        return SkillSwapSession.objects.filter(
            teacher=self.request.user
        ) | SkillSwapSession.objects.filter(
            learner=self.request.user
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all sessions for the user
        all_sessions = SkillSwapSession.objects.filter(
            teacher=user
        ) | SkillSwapSession.objects.filter(
            learner=user
        )
        
        # Categorize sessions
        context['upcoming_sessions'] = all_sessions.filter(status='scheduled').order_by('scheduled_date')
        context['ongoing_sessions'] = all_sessions.filter(status='in_progress').order_by('scheduled_date')
        context['completed_sessions'] = all_sessions.filter(status='completed').order_by('-ended_at')
        
        # Get pending requests that need approval (requests sent to this user)
        context['pending_requests'] = SkillSwapRequest.objects.filter(
            recipient=user,
            status='pending'
        ).select_related('requester', 'offered_skill__skill').order_by('-created_at')
        
        return context


class UpcomingSessionListView(LoginRequiredMixin, ListView):
    model = SkillSwapSession
    template_name = 'skill_sessions/upcoming_sessions.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        return SkillSwapSession.objects.filter(
            scheduled_date__gte=timezone.now()
        ).filter(
            teacher=self.request.user
        ) | SkillSwapSession.objects.filter(
            scheduled_date__gte=timezone.now()
        ).filter(
            learner=self.request.user
        )


class SessionHistoryView(LoginRequiredMixin, ListView):
    model = SkillSwapSession
    template_name = 'skill_sessions/session_history.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        return SkillSwapSession.objects.filter(
            scheduled_date__lt=timezone.now()
        ).filter(
            teacher=self.request.user
        ) | SkillSwapSession.objects.filter(
            scheduled_date__lt=timezone.now()
        ).filter(
            learner=self.request.user
        )


class SessionDetailView(LoginRequiredMixin, DetailView):
    model = SkillSwapSession
    template_name = 'skill_sessions/session_detail.html'
    context_object_name = 'session'
    
    def get_queryset(self):
        return SkillSwapSession.objects.filter(
            teacher=self.request.user
        ) | SkillSwapSession.objects.filter(
            learner=self.request.user
        )


class SessionUpdateView(LoginRequiredMixin, UpdateView):
    model = SkillSwapSession
    form_class = SessionScheduleForm
    template_name = 'skill_sessions/session_form.html'
    success_url = reverse_lazy('skill_sessions:session_list')
    
    def get_queryset(self):
        return SkillSwapSession.objects.filter(
            teacher=self.request.user
        ) | SkillSwapSession.objects.filter(
            learner=self.request.user
        )


@login_required
def cancel_session(request, pk):
    session = get_object_or_404(SkillSwapSession, pk=pk)
    session.status = 'cancelled'
    session.save()
    return redirect('skill_sessions:session_list')


@login_required
def start_session(request, pk):
    session = get_object_or_404(SkillSwapSession, pk=pk)
    session.status = 'in_progress'
    session.started_at = timezone.now()
    session.save()
    return redirect('skill_sessions:session_detail', pk=pk)


@login_required
def end_session(request, pk):
    session = get_object_or_404(SkillSwapSession, pk=pk)
    session.status = 'completed'
    session.ended_at = timezone.now()
    session.save()
    return redirect('skill_sessions:session_detail', pk=pk)


class SessionReviewCreateView(LoginRequiredMixin, CreateView):
    model = SessionReview
    form_class = SessionReviewForm
    template_name = 'skill_sessions/review_form.html'
    success_url = reverse_lazy('skill_sessions:session_list')
    
    def form_valid(self, form):
        session = get_object_or_404(SkillSwapSession, pk=self.kwargs['session_id'])
        form.instance.session = session
        form.instance.reviewer = self.request.user
        if self.request.user == session.teacher:
            form.instance.reviewee = session.learner
        else:
            form.instance.reviewee = session.teacher
        return super().form_valid(form)


class SessionReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = SessionReview
    form_class = SessionReviewForm
    template_name = 'skill_sessions/review_form.html'
    success_url = reverse_lazy('skill_sessions:review_list')
    
    def get_queryset(self):
        return SessionReview.objects.filter(reviewer=self.request.user)


class ReviewListView(LoginRequiredMixin, ListView):
    model = SessionReview
    template_name = 'skill_sessions/review_list.html'
    context_object_name = 'reviews'
    
    def get_queryset(self):
        return SessionReview.objects.filter(
            reviewer=self.request.user
        ) | SessionReview.objects.filter(
            reviewee=self.request.user
        )


class CalendarView(LoginRequiredMixin, ListView):
    model = SkillSwapSession
    template_name = 'skill_sessions/calendar.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        return SkillSwapSession.objects.filter(
            teacher=self.request.user
        ) | SkillSwapSession.objects.filter(
            learner=self.request.user
        )


class ScheduleSessionView(LoginRequiredMixin, CreateView):
    model = SkillSwapSession
    form_class = SessionScheduleForm
    template_name = 'skill_sessions/schedule_session.html'
    success_url = reverse_lazy('skill_sessions:session_list')
    
    def form_valid(self, form):
        request_obj = get_object_or_404(SkillSwapRequest, pk=self.kwargs['request_id'])
        form.instance.request = request_obj
        form.instance.teacher = request_obj.recipient
        form.instance.learner = request_obj.requester
        form.instance.skill = request_obj.offered_skill.skill
        return super().form_valid(form)


class SessionManagementView(LoginRequiredMixin, ListView):
    model = SkillSwapSession
    template_name = 'skill_sessions/session_management.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        # Get all sessions where user is involved (either as teacher or learner)
        return SkillSwapSession.objects.filter(
            models.Q(teacher=self.request.user) | models.Q(learner=self.request.user)
        ).select_related('skill', 'teacher', 'learner', 'request')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all sessions where user is involved
        all_sessions = SkillSwapSession.objects.filter(
            models.Q(teacher=user) | models.Q(learner=user)
        ).select_related('skill', 'teacher', 'learner', 'request')
        
        # Categorize sessions
        completed_sessions = all_sessions.filter(status='completed')
        ongoing_sessions = all_sessions.filter(status='in_progress')
        upcoming_sessions = all_sessions.filter(status='scheduled', scheduled_date__gt=timezone.now())
        
        # Get pending approval sessions (requests that haven't been responded to)
        pending_requests = SkillSwapRequest.objects.filter(
            recipient=user,
            status='pending'
        ).select_related('requester', 'offered_skill')
        
        # Convert pending requests to session-like objects for display
        pending_sessions = []
        for request in pending_requests:
            # Create a mock session object for display purposes
            mock_session = type('MockSession', (), {
                'id': request.id,
                'skill': request.offered_skill.skill,
                'learner': request.requester,
                'scheduled_date': timezone.now(),  # Placeholder
                'duration_minutes': request.proposed_duration,
                'request': request,
                'status': 'pending_approval'
            })()
            pending_sessions.append(mock_session)
        
        context.update({
            'completed_sessions': completed_sessions,
            'ongoing_sessions': ongoing_sessions,
            'upcoming_sessions': upcoming_sessions,
            'pending_sessions': pending_sessions,
            'completed_count': completed_sessions.count(),
            'ongoing_count': ongoing_sessions.count(),
            'upcoming_count': upcoming_sessions.count(),
            'pending_count': len(pending_sessions),
        })
        
        return context


@login_required
def approve_session(request, session_id):
    """Approve a session request"""
    if request.method == 'POST':
        # Get the request object (not session, since it's pending)
        swap_request = get_object_or_404(SkillSwapRequest, id=session_id, recipient=request.user, status='pending')
        
        # Update request status
        swap_request.status = 'accepted'
        swap_request.responded_at = timezone.now()
        swap_request.save()
        
        # Create a session
        session = SkillSwapSession.objects.create(
            request=swap_request,
            teacher=swap_request.recipient,  # The person who approved is the teacher
            learner=swap_request.requester,
            skill=swap_request.offered_skill.skill,
            scheduled_date=timezone.now() + timezone.timedelta(days=1),  # Default to tomorrow
            duration_minutes=swap_request.proposed_duration,
            format=swap_request.proposed_format,
            location=swap_request.proposed_location,
            status='scheduled'
        )
        
        messages.success(request, f'Session approved! You can now schedule the details with {swap_request.requester.username}.')
    
    return redirect('skill_sessions:session_management')


@login_required  
def reject_session(request, session_id):
    """Reject a session request"""
    if request.method == 'POST':
        # Get the request object (not session, since it's pending)
        swap_request = get_object_or_404(SkillSwapRequest, id=session_id, recipient=request.user, status='pending')
        
        # Update request status
        swap_request.status = 'declined'
        swap_request.responded_at = timezone.now()
        swap_request.save()
        
        messages.info(request, f'Session request from {swap_request.requester.username} has been rejected.')
    
    return redirect('skill_sessions:session_management')
