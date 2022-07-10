from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', include('posts.urls', namespace='posts')),
    path('admin/', admin.site.urls),
    # Django проверяет url-адреса сверху вниз,
    # нам нужно, чтобы Django сначала проверял адреса в приложении users
    path('auth/', include('users.urls')),
    # Если какой-то URL не обнаружится в приложении users —
    # Django пойдёт искать его в django.contrib.auth
    path('auth/', include('django.contrib.auth.urls')),  # подключили к
    # головному - urls.py проекта Yatube файл
    # urls.py модуля django.contrib.auth
    # подключили новое приложение about в головной urls
    path('about/', include('about.urls', namespace='about')),
]

handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'
handler403 = 'core.views.csrf_failure'

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )