from django.urls import path
from . import views

app_name = 'brand_assets'

urlpatterns = [
    path('', views.asset_library, name='library'),
    path('download/<int:asset_id>/', views.download_asset, name='download'),
]
