from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author_name', 'published_at', 'is_published']
    list_filter = ['is_published', 'category']
    search_fields = ['title', 'author_name', 'category']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    ordering = ['-published_at']
