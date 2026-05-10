"""
URL configuration for aitmatov_digital project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/auth/', include('users.urls')),
    path('api/users/', include('users.urls_users')),
    path('api/subjects/', include('subjects.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/aitmatov/', include('aitmatov.urls')),
    path('api/progress/', include('progress.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
