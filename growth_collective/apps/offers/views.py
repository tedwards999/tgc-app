from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from .models import Offer, OfferEngagement, OFFER_CATEGORY_CHOICES
from .forms import OfferForm
from apps.points.services import award_points


@login_required
def offer_list(request):
    from django.db.models import Q
    category = request.GET.get('category', '')
    now = timezone.now()
    offers = Offer.objects.filter(is_active=True).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=now)
    )

    if category:
        offers = offers.filter(category=category)

    user_has_premium = request.user.has_premium_access()

    # Track which offers user has already engaged
    engaged_ids = set(
        OfferEngagement.objects.filter(user=request.user)
        .values_list('offer_id', flat=True)
    )
    for offer in offers:
        offer.user_engaged = offer.pk in engaged_ids
        offer.user_can_access = not offer.is_premium or user_has_premium

    if request.htmx:
        return render(request, 'offers/partials/offer_grid.html', {
            'offers': offers,
            'user_has_premium': user_has_premium,
        })

    return render(request, 'offers/offers.html', {
        'offers': offers,
        'categories': OFFER_CATEGORY_CHOICES,
        'active_category': category,
        'user_has_premium': user_has_premium,
        'featured': offers.filter(is_featured=True)[:3],
    })


@login_required
def offer_detail(request, offer_id):
    now = timezone.now()
    offer = get_object_or_404(Offer, pk=offer_id, is_active=True)

    if offer.expires_at and offer.expires_at < now:
        messages.warning(request, 'This offer has expired.')
        return redirect('offers:list')

    if offer.is_premium and not request.user.has_premium_access():
        messages.warning(request, 'This offer is for premium members only.')
        return redirect('billing:pricing')

    return render(request, 'offers/offer_detail.html', {
        'offer': offer,
    })


@login_required
def redeem_offer(request, offer_id):
    offer = get_object_or_404(Offer, pk=offer_id, is_active=True)

    if offer.is_premium and not request.user.has_premium_access():
        messages.warning(request, 'This offer is for premium members only.')
        return redirect('billing:pricing')

    engagement, created = OfferEngagement.objects.get_or_create(
        offer=offer,
        user=request.user,
    )

    if created:
        award_points(request.user, 'offer_engaged', f'Engaged with offer: {offer.title}')

    if offer.redemption_url:
        return redirect(offer.redemption_url)

    return render(request, 'offers/redeem.html', {'offer': offer})


@login_required
def create_offer(request):
    form = OfferForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        offer = form.save(commit=False)
        offer.submitted_by = request.user
        offer.is_active = True
        offer.save()
        award_points(request.user, 'offer_posted', f'Submitted offer: {offer.title}')
        messages.success(request, 'Your offer has been submitted for review. We\'ll publish it shortly.')
        return redirect('offers:list')

    return render(request, 'offers/create_offer.html', {'form': form})
