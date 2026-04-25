import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import BrandAsset, CATEGORY_CHOICES

logger = logging.getLogger(__name__)


@login_required
def asset_library(request):
    category = request.GET.get('category', '')
    assets = BrandAsset.objects.filter(is_active=True)

    if category:
        assets = assets.filter(category=category)

    # Mark premium assets the user can't access
    user_has_premium = request.user.has_premium_access()
    for asset in assets:
        asset.user_can_download = not asset.is_premium or user_has_premium

    if request.htmx:
        return render(request, 'brand_assets/partials/asset_grid.html', {
            'assets': assets,
            'user_has_premium': user_has_premium,
        })

    return render(request, 'brand_assets/library.html', {
        'assets': assets,
        'categories': CATEGORY_CHOICES,
        'active_category': category,
        'user_has_premium': user_has_premium,
    })


@login_required
def download_asset(request, asset_id):
    asset = get_object_or_404(BrandAsset, pk=asset_id, is_active=True)

    if asset.is_premium and not request.user.has_premium_access():
        messages.warning(request, 'This asset requires a premium membership.')
        return redirect('billing:pricing')

    # Atomic increment
    BrandAsset.objects.filter(pk=asset_id).update(download_count=F('download_count') + 1)

    # Generate a fresh signed URL (or plain local URL in dev)
    try:
        if getattr(settings, 'USE_SPACES', False):
            from storages.backends.s3boto3 import S3Boto3Storage
            storage = S3Boto3Storage()
            file_url = storage.url(asset.file.name)
        else:
            file_url = asset.file.url
        return redirect(file_url)
    except Exception:
        logger.exception('Failed to generate download URL for asset %s', asset_id)
        messages.error(request, 'Download failed. Please try again.')
        return redirect('brand_assets:library')
