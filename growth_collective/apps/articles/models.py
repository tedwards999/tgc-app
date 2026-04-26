from django.db import models
from django.utils.text import slugify


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.CharField(max_length=100)
    excerpt = models.TextField(max_length=300)
    body = models.TextField()
    cover_image = models.ImageField(upload_to='articles/', blank=True, null=True)
    author_name = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
