from django.urls import path
from .views import (
    RegisterView, 
    CustomAuthToken, 
    UserDetailView, 
    ConnectPlanfixView, 
    DisconnectPlanfixView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('connect-planfix/', ConnectPlanfixView.as_view(), name='connect-planfix'),
    path('disconnect-planfix/', DisconnectPlanfixView.as_view(), name='disconnect-planfix'),
]