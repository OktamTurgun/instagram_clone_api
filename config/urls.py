from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API endpoints
    path("api/auth/",   include("accounts.urls")),
    path("api/social/", include("social.urls")),
    path("api/posts/",  include("posts.urls")),

    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # ReDoc
    path("api/redoc/",  SpectacularRedocView.as_view(url_name="schema"),   name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)