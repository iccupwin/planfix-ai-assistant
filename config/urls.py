from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/planfix/', include('planfix_integration.urls')),
    path('api/claude/', include('claude_integration.urls')),
    path('api/vector-db/', include('vector_db.urls')),
    path('api/chat/', include('chat.urls')),
    
    # Frontend (React) routes
    path('', TemplateView.as_view(template_name='index.html')),
    path('chat/', TemplateView.as_view(template_name='index.html')),
    path('chat/<str:chat_id>/', TemplateView.as_view(template_name='index.html')),
    path('settings/', TemplateView.as_view(template_name='index.html')),
    path('login/', TemplateView.as_view(template_name='index.html')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)