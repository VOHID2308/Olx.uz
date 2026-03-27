"""
Kategoriya modeli - ierarxik tuzilish (parent-child)
"""

from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """
    Kategoriya modeli.
    Ierarxik tuzilish: parent-child munosabat.
    Masalan: Elektronika > Telefonlar > iPhone
    """

    name = models.CharField(max_length=200, verbose_name='Nomi')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Ota kategoriya'
    )
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True, verbose_name='Ikonka')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    is_active = models.BooleanField(default=True, verbose_name='Faolmi')
    order_num = models.PositiveIntegerField(default=0, verbose_name='Tartib raqami')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        ordering = ['order_num', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        """Slug avtomatik yaratish"""
        if not self.slug:
            self.slug = slugify(self.name)
            # Unique slug ta'minlash
            original_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def is_root(self):
        """Asosiy kategoriyami (parent yo'q)?"""
        return self.parent is None

    def get_children(self):
        """Barcha bolalar kategoriyalar"""
        return self.children.filter(is_active=True)

    def get_all_products_count(self):
        """Shu kategoriya va barcha sub-kategoriyalardagi mahsulotlar soni"""
        count = self.products.filter(status='aktiv').count()
        for child in self.get_children():
            count += child.get_all_products_count()
        return count