"""
Reviews app modeli - fikr va reyting
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Review(models.Model):
    """
    Fikr va reyting modeli.
    Faqat 'sotib olingan' statusli buyurtma uchun.
    Har bir buyurtma uchun bitta fikr (OneToOne).
    """

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Buyurtma'
    )
    reviewer = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='given_reviews',
        verbose_name='Fikr qoldiruvchi'
    )
    seller = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='received_reviews',
        verbose_name='Sotuvchi'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Reyting (1-5)'
    )
    comment = models.TextField(verbose_name='Fikr')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')

    class Meta:
        verbose_name = 'Fikr'
        verbose_name_plural = 'Fikrlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"Reyting {self.rating}/5 - {self.reviewer.full_name} -> {self.seller.full_name}"

    def save(self, *args, **kwargs):
        """Fikr saqlangandan keyin sotuvchi reytingini yangilash"""
        super().save(*args, **kwargs)
        # Sotuvchi profilining reytingini yangilash
        if hasattr(self.seller, 'seller_profile'):
            self.seller.seller_profile.update_rating()