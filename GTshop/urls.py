from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views


# ═══════════════════════════════════════════════════════════════════════
# CartAwareLoginView — giữ giỏ hàng khi đăng nhập
# ═══════════════════════════════════════════════════════════════════════
class CartAwareLoginView(auth_views.LoginView):
    def form_valid(self, form):
        self.request._pre_login_cart = dict(
            self.request.session.get('cart', {})
        )
        return super().form_valid(form)


# ═══════════════════════════════════════════════════════════════════════
# URL patterns — KHÔNG dùng i18n_patterns
#
# Lý do: i18n_patterns thêm prefix /en/, /ja/... vào URL.
# LocaleMiddleware ưu tiên URL prefix hơn cookie → switching
# ngôn ngữ bị reset về mặc định khi redirect về /.
#
# Giải pháp: Dùng urlpatterns thường + i18n/ endpoint.
# Ngôn ngữ được detect từ cookie/session bởi LocaleMiddleware.
# ═══════════════════════════════════════════════════════════════════════
urlpatterns = [
    path('admin/', admin.site.urls),

    # set_language endpoint — PHẢI có để dropdown ngôn ngữ hoạt động
    path('i18n/', include('django.conf.urls.i18n')),

    # App URLs — không có prefix ngôn ngữ
    path('', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('blog/', include('blog.urls')),
    path('stats/', include('carts.stats_urls')),

    # Auth
    path('accounts/login/',    CartAwareLoginView.as_view(),    name='login'),
    path('accounts/logout/',   auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', accounts_views.register,          name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)