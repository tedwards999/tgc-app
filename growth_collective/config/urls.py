from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.core.urls')),
    path('dashboard/', include('apps.accounts.urls')),
    path('billing/', include('apps.billing.urls')),
    path('coaching/', include('apps.bookings.urls')),
    path('events/', include('apps.events.urls')),
    path('resources/', include('apps.brand_assets.urls')),
    path('deal-board/', include('apps.referrals.urls')),
    path('offers/', include('apps.offers.urls')),
    path('points/', include('apps.points.urls')),
    path('pages/', include('apps.content.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
