"""
Orders app modeli - buyurtmalar
"""

from django.db import models


class Order(models.Model):
    """
    Buyurtma modeli.
    Xaridor mahsulot uchun buyurtma beradi.
    """

    class Status(models.TextChoices):
        KUTILYAPTI = 'kutilyapti', 'Kutilyapti'
        KELISHILGAN = 'kelishilgan', 'Kelishilgan'
        SOTIB_OLINGAN = 'sotib olingan', 'Sotib olingan'
        BEKOR_QILINGAN = 'bekor qilingan', 'Bekor qilingan'

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Mahsulot'
    )
    buyer = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='buyer_orders',
        verbose_name='Xaridor'
    )
    seller = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='seller_orders',
        verbose_name='Sotuvchi'
    )
    final_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Kelishilgan narx'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.KUTILYAPTI,
        verbose_name='Status'
    )
    meeting_location = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Uchrashuv joyi'
    )
    meeting_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Uchrashuv vaqti'
    )
    notes = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')

    class Meta:
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} - {self.buyer.full_name} -> {self.product.title}"

    def save(self, *args, **kwargs):
        """final_price avtomatik belgilash"""
        if not self.pk and not self.final_price:
            self.final_price = self.product.price
        super().save(*args, **kwargs)

    def complete_purchase(self):
        """
        Buyurtmani yakunlash:
        - Status -> sotib olingan
        - Mahsulot -> sotilgan
        - Sotuvchining total_sales +1
        """
        self.status = self.Status.SOTIB_OLINGAN
        self.save(update_fields=['status'])

        # Mahsulotni sotilgan deb belgilash
        self.product.mark_as_sold()