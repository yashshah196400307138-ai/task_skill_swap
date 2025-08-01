from django.urls import path
from . import views

app_name = 'skill_sessions'

urlpatterns = [
    # Request management
    path('requests/', views.RequestListView.as_view(), name='request_list'),
    path('requests/sent/', views.SentRequestListView.as_view(), name='sent_requests'),
    path('requests/received/', views.ReceivedRequestListView.as_view(), name='received_requests'),
    path('requests/send/<int:user_id>/', views.SendRequestView.as_view(), name='send_request'),
    path('requests/<int:pk>/', views.RequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/respond/', views.RequestResponseView.as_view(), name='request_respond'),
    path('requests/<int:pk>/cancel/', views.cancel_request, name='request_cancel'),
    
    # Session management
    path('', views.SessionListView.as_view(), name='session_list'),
    path('manage/', views.SessionManagementView.as_view(), name='session_management'),
    path('approve/<int:session_id>/', views.approve_session, name='approve_session'),
    path('reject/<int:session_id>/', views.reject_session, name='reject_session'),
    path('upcoming/', views.UpcomingSessionListView.as_view(), name='upcoming_sessions'),
    path('history/', views.SessionHistoryView.as_view(), name='session_history'),
    path('<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('<int:pk>/edit/', views.SessionUpdateView.as_view(), name='session_edit'),
    path('<int:pk>/cancel/', views.cancel_session, name='session_cancel'),
    path('<int:pk>/start/', views.start_session, name='session_start'),
    path('<int:pk>/end/', views.end_session, name='session_end'),
    
    # Reviews
    path('<int:session_id>/review/', views.SessionReviewCreateView.as_view(), name='review_create'),
    path('reviews/<int:pk>/edit/', views.SessionReviewUpdateView.as_view(), name='review_edit'),
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    
    # Calendar and scheduling
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('schedule/<int:request_id>/', views.ScheduleSessionView.as_view(), name='schedule_session'),
]