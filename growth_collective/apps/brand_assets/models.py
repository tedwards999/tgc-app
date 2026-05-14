from django.db import models


ACCESS_CHOICES = [
    ('all_members', 'All Members'),
    ('premium_only', 'Premium Only'),
]

CATEGORY_CHOICES = [
    ('logo', 'Logo'),
    ('colour_palette', 'Colour Palette'),
    ('typography', 'Typography'),
    ('templates', 'Templates'),
    ('guidelines', 'Guidelines'),
    ('other', 'Other'),
]


class BrandAsset(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='all_members')
    file = models.FileField(upload_to='brand_assets/')
    preview_image = models.ImageField(upload_to='brand_assets/previews/', blank=True)
    file_size_bytes = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'title']

    def __str__(self):
        return f'{self.title} ({self.get_category_display()})'

    def save(self, *args, **kwargs):
        if self.file and self.file_size_bytes == 0:
            try:
                self.file_size_bytes = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def is_premium(self):
        return self.access_level == 'premium_only'

    @property
    def file_size_display(self):
        size = self.file_size_bytes
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        else:
            return f'{size / (1024 * 1024):.1f} MB'
