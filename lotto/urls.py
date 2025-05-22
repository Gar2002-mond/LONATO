from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gestloto.urls')),
   
    path('accounts/', include('django.contrib.auth.urls')), # Inclut login, logout, password_reset, etc.
    path('schema-viewer/',include('schema_viewer.urls')),
   # Pour la visualisation du schéma de la base de données
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 