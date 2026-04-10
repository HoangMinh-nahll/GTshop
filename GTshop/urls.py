from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views


# ═══════════════════════════════════════════════════════════════════════
# CartAwareLoginView
# ───────────────────────────────────────────────────────────────────────
# Vấn đề: Django tự đổi session key khi login() để bảo mật
#         → giỏ hàng session cũ bị mất sau khi đăng nhập
#
# Giải pháp: Lưu cart vào request._pre_login_cart trước khi login,
#            signal user_logged_in trong accounts/signals.py
#            sẽ đặt lại cart vào session mới.
# ═══════════════════════════════════════════════════════════════════════
class CartAwareLoginView(auth_views.LoginView):
    def form_valid(self, form):
        # Lưu giỏ hàng TRƯỚC khi Django rotate session key
        self.request._pre_login_cart = dict(
            self.request.session.get('cart', {})
        )
        return super().form_valid(form)





# ─── URL không cần prefix ngôn ngữ ──────────────────────────────────
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]

# ─── URL có prefix ngôn ngữ ──────────────────────────────────────────
urlpatterns += i18n_patterns(
    path('', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('blog/', include('blog.urls')),

    # Thống kê (chỉ staff)
    path('stats/', include('carts.stats_urls')),

    # Auth — CartAwareLoginView giữ giỏ hàng sau login
    path('accounts/login/',    CartAwareLoginView.as_view(),    name='login'),
    path('accounts/logout/',   auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', accounts_views.register,          name='register'),

    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)