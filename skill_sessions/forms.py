from django import forms
from django.contrib.auth.models import User
from .models import SkillSwapRequest, SkillSwapSession, SessionReview
from skills.models import OfferedSkill, DesiredSkill

class SkillSwapRequestForm(forms.ModelForm):
    """Form for creating skill swap requests"""
    
    class Meta:
        model = SkillSwapRequest
        fields = ['message', 'proposed_duration', 'proposed_format', 'proposed_location']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Introduce yourself and explain why you\'d like to learn this skill...'
            }),
            'proposed_location': forms.TextInput(attrs={
                'placeholder': 'e.g., Library, Coffee Shop, Online'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester', None)
        self.recipient = kwargs.pop('recipient', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        if self.requester and self.recipient:
            # Check if there's already a pending request
            existing = SkillSwapRequest.objects.filter(
                requester=self.requester,
                recipient=self.recipient,
                status='pending'
            )
            if existing.exists():
                raise forms.ValidationError('You already have a pending request with this user.')
        
        return cleaned_data


class RequestResponseForm(forms.Form):
    """Form for responding to skill swap requests"""
    response_message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Optional message to the requester...'
        }),
        required=False
    )
    proposed_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False,
        help_text="If accepting, propose a date and time"
    )
    proposed_location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Meeting location'})
    )


class SessionScheduleForm(forms.ModelForm):
    """Form for scheduling sessions"""
    
    class Meta:
        model = SkillSwapSession
        fields = ['scheduled_date', 'duration_minutes', 'format', 'location', 'meeting_link']
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'placeholder': 'Meeting location'}),
            'meeting_link': forms.URLInput(attrs={'placeholder': 'https://meet.google.com/...'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        format_type = cleaned_data.get('format')
        meeting_link = cleaned_data.get('meeting_link')
        
        if scheduled_date:
            from django.utils import timezone
            if scheduled_date <= timezone.now():
                raise forms.ValidationError('Session must be scheduled for a future date and time.')
        
        if format_type == 'online' and not meeting_link:
            raise forms.ValidationError('Meeting link is required for online sessions.')
        
        return cleaned_data


class SessionReviewForm(forms.ModelForm):
    """Form for creating session reviews"""
    
    class Meta:
        model = SessionReview
        fields = [
            'overall_rating', 'communication_rating', 'knowledge_rating', 
            'punctuality_rating', 'review_text', 'what_learned', 'suggestions',
            'would_recommend', 'is_anonymous', 'is_public'
        ]
        widgets = {
            'review_text': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your experience with this session...'
            }),
            'what_learned': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What did you learn or teach?'
            }),
            'suggestions': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Any suggestions for improvement?'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        overall_rating = cleaned_data.get('overall_rating')
        review_text = cleaned_data.get('review_text')
        
        if overall_rating and overall_rating < 3 and not review_text:
            raise forms.ValidationError('Please provide feedback when giving a low rating.')
        
        return cleaned_data


class SessionFilterForm(forms.Form):
    """Form for filtering sessions"""
    status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        required=False
    )
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    format_type = forms.ChoiceField(
        choices=[
            ('', 'All Formats'),
            ('online', 'Online'),
            ('in_person', 'In-Person'),
        ],
        required=False
    ) 