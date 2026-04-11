from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from accounts import views as accounts_views
from accounts.account_views import my_account, chatbot_api


# ═══════════════════════════════════════════════════════════════════════
# CartAwareLoginView — giữ giỏ hàng khi đăng nhập
# ═══════════════════════════════════════════════════════════════════════
class CartAwareLoginView(auth_views.LoginView):
    def form_valid(self, form):
        # Lưu giỏ hàng trước khi đăng nhập
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
    # Admin
    path('admin/', admin.site.urls),

    # set_language endpoint — PHẢI có để dropdown ngôn ngữ hoạt động
    path('i18n/', include('django.conf.urls.i18n')),

    # App URLs — không có prefix ngôn ngữ
    path('', include('store.urls')),           # Trang chủ và store
    path('cart/', include('carts.urls')),      # Giỏ hàng
    path('blog/', include('blog.urls')),       # Blog
    path('stats/', include('carts.stats_urls')), # Thống kê giỏ hàng

    # Authentication URLs
    path('accounts/login/',    CartAwareLoginView.as_view(),    name='login'),
    path('accounts/logout/',   auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', accounts_views.register,         name='register'),
    
    # My Account - profile page
    path('accounts/profile/',  my_account,                      name='account:my_account'),
    path('accounts/me/',       my_account,                      name='my_account'),  # Alias đơn giản
    
    # Chatbot API proxy (gọi Anthropic từ backend để bảo mật API key)
    path('api/chat/',          chatbot_api,                     name='chatbot_api'),
]


# ═══════════════════════════════════════════════════════════════════════
# Debug mode - static/media serving
# ═══════════════════════════════════════════════════════════════════════
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)