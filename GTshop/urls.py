from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views

# ─── PHẢI đặt i18n ngoài i18n_patterns ───────────────────────────────────────
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # ← set_language endpoint
]

# ─── Các URL có hỗ trợ đa ngôn ngữ ──────────────────────────────────────────
urlpatterns += i18n_patterns(
    path('', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('blog/', include('blog.urls')),
    path('accounts/login/',    auth_views.LoginView.as_view(),  name='login'),
    path('accounts/logout/',   auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', accounts_views.register,          name='register'),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)