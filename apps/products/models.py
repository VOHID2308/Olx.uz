"""
Products app modellari - Product, ProductImage, Favorite
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class Product(models.Model):
    """
    Mahsulot/E'lon modeli
    """

    class Status(models.TextChoices):
        MODERATSIYADA = 'moderatsiyada', 'Moderatsiyada'
        AKTIV = 'aktiv', 'Aktiv'
        RAD_ETILGAN = 'rad etilgan', 'Rad etilgan'
        SOTILGAN = 'sotilgan', 'Sotilgan'
        ARXIVLANGAN = 'arxivlangan', 'Arxivlangan'

    class Condition(models.TextChoices):
        YANGI = 'yangi', 'Yangi'
        IDEAL = 'ideal', 'Ideal'
        YAXSHI = 'yaxshi', 'Yaxshi'
        QONIQARLI = 'qoniqarli', 'Qoniqarli'

    class PriceType(models.TextChoices):
        QATIY = "qat'iy", "Qat'iy"
        KELISHILADI = 'kelishiladi', 'Kelishiladi'
        BEPUL = 'bepul', 'Bepul'
        AYIRBOSHLASH = 'ayirboshlash', 'Ayirboshlash'

    seller = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Sotuvchi'
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Kategoriya'
    )
    title = models.CharField(max_length=200, verbose_name='Sarlavha')
    description = models.TextField(verbose_name='Tavsif')
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        verbose_name='Holati'
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Narxi')
    price_type = models.CharField(
        max_length=20,
        choices=PriceType.choices,
        default=PriceType.QATIY,
        verbose_name='Narx turi'
    )
    region = models.CharField(max_length=100, verbose_name='Viloyat')
    district = models.CharField(max_length=100, verbose_name='Tuman')
    view_count = models.PositiveIntegerField(default=0, verbose_name='Ko\'rishlar soni')
    favorite_count = models.PositiveIntegerField(default=0, verbose_name='Sevimlilar soni')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.MODERATSIYADA,
        verbose_name='Status'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='Nashr vaqti')
    expires_at = models.DateTimeField(verbose_name='Tugash vaqti')

    class Meta:
        verbose_name = 'Mahsulot'
        verbose_name_plural = 'Mahsulotlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.seller.full_name}"

    def save(self, *args, **kwargs):
        """expires_at avtomatik belgilash (30 kun)"""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def main_image(self):
        """Asosiy rasm"""
        return self.images.filter(is_main=True).first()

    def publish(self):
        """E'lonni aktiv qilish"""
        self.status = self.Status.AKTIV
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at'])

    def archive(self):
        """E'lonni arxivlash"""
        self.status = self.Status.ARXIVLANGAN
        self.save(update_fields=['status'])

    def mark_as_sold(self):
        """E'lonni sotilgan deb belgilash"""
        self.status = self.Status.SOTILGAN
        self.save(update_fields=['status'])
        if hasattr(self.seller, 'seller_profile'):
            self.seller.seller_profile.total_sales += 1
            self.seller.seller_profile.save(update_fields=['total_sales'])


class ProductImage(models.Model):
    """
    Mahsulot rasmlari.
    Har bir mahsulotda bir nechta rasm bo'lishi mumkin.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Mahsulot'
    )
    image = models.ImageField(upload_to='product_images/', verbose_name='Rasm')
    order = models.PositiveIntegerField(default=0, verbose_name='Tartib')
    is_main = models.BooleanField(default=False, verbose_name='Asosiy rasm')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')

    class Meta:
        verbose_name = 'Mahsulot rasmi'
        verbose_name_plural = 'Mahsulot rasmlari'
        ordering = ['order']

    def __str__(self):
        return f"{self.product.title} - rasm {self.order}"

    def save(self, *args, **kwargs):
        """Agar is_main=True bo'lsa, boshqalarni False qilish"""
        if self.is_main:
            ProductImage.objects.filter(
                product=self.product,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)


class Favorite(models.Model):
    """
    Sevimli mahsulotlar.
    User va Product juftligi unique bo'lishi kerak.
    """

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Foydalanuvchi'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Mahsulot'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Qo\'shilgan sana')

    class Meta:
        verbose_name = 'Sevimli'
        verbose_name_plural = 'Sevimlilar'
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.product.title}"

    def save(self, *args, **kwargs):
        """Sevimlilarga qo'shilganda favorite_count ni oshirish"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.product.favorite_count += 1
            self.product.save(update_fields=['favorite_count'])

    def delete(self, *args, **kwargs):
        """Sevimlilardan o'chirilganda favorite_count ni kamaytirish"""
        product = self.product
        super().delete(*args, **kwargs)
        if product.favorite_count > 0:
            product.favorite_count -= 1
            product.save(update_fields=['favorite_count'])