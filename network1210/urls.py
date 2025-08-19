from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts.views import signup
from accounts.views import custom_logout
from accounts.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('network/', include('network.urls')),  # visualization_home 포함
    path('signup/', signup, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),  # ✅ 변경
]

# MEDIA 파일 제공 설정 (DEBUG 모드에서만 사용)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

