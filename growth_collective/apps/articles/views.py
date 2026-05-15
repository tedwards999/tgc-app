from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import Article, Category


@login_required
def article_list(request):
    category_id = request.GET.get('category', '')
    articles = Article.objects.filter(is_published=True).select_related('category')
    if category_id:
        articles = articles.filter(category_id=category_id)

    categories = Category.objects.all()

    return render(request, 'articles/article_list.html', {
        'articles': articles,
        'categories': categories,
        'active_category': category_id,
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
