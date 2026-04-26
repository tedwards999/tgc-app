from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import Article


@login_required
def article_list(request):
    category = request.GET.get('category', '')
    articles = Article.objects.filter(is_published=True)
    if category:
        articles = articles.filter(category__iexact=category)

    categories = Article.objects.filter(is_published=True).values_list('category', flat=True).distinct()

    return render(request, 'articles/article_list.html', {
        'articles': articles,
        'categories': categories,
        'active_category': category,
    })


@login_required
def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    return render(request, 'articles/article_detail.html', {'article': article})


@login_required
def article_pdf(request, slug):
    from weasyprint import HTML
    from django.template.loader import render_to_string

    article = get_object_or_404(Article, slug=slug, is_published=True)
    html_string = render_to_string('articles/article_pdf.html', {'article': article}, request=request)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{article.slug}.pdf"'
    return response
